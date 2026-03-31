import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import date

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.settings import get_conn


DAY_OPTIONS = [
    (0, "日"),
    (1, "月"),
    (2, "火"),
    (3, "水"),
    (4, "木"),
    (5, "金"),
    (6, "土"),
]
DB_OPEN_END_DATE = date(9999, 12, 31)
STREAMLIT_MAX_DATE = date(2099, 12, 31)


def _day_label(day_num: int) -> str:
    for value, label in DAY_OPTIONS:
        if value == day_num:
            return label
    return str(day_num)


def _safe_index(df: pd.DataFrame, column: str, value, default: int = 0) -> int:
    matched = df.index[df[column] == value].tolist()
    if not matched:
        return int(default)
    return int(matched[0])


def _safe_option_index(options: list, value, default: int = 0) -> int:
    try:
        return int(options.index(value))
    except ValueError:
        return int(default)


def _safe_date_value(value, fallback: date) -> date:
    if value is None or pd.isna(value):
        return fallback
    if isinstance(value, date):
        return value
    text = str(value)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return fallback


def _safe_date_for_widget(value: date) -> date:
    if value > STREAMLIT_MAX_DATE:
        return STREAMLIT_MAX_DATE
    return value


def _safe_day_of_week(value, default: int = 1) -> int:
    if value is None or pd.isna(value):
        return default
    text = str(value).strip()
    if text == "":
        return default
    try:
        day_num = int(float(text))
    except ValueError:
        return default
    valid_days = [v for v, _ in DAY_OPTIONS]
    return day_num if day_num in valid_days else default


st.title("枠管理")
conn = get_conn()

slot_df = pd.read_sql(
    """
    SELECT
        cs.SlotID,
        cs.Rpt1ClinDeptID,
        cd.ClinDeptName,
        cs.Rpt1SpecialtyID,
        sp.SpecialtyName,
        cs.Rpt2ClinDeptID,
        rcd2.RptClinDeptName AS Rpt2ClinDeptName,
        cs.Rpt3ClinDeptID,
        rcd3.RptClinDeptName AS Rpt3ClinDeptName,
        cs.Rpt4ClinDeptID,
        rcd4.RptClinDeptName AS Rpt4ClinDeptName,
        cs.Rpt5ClinDeptID,
        rcd5.RptClinDeptName AS Rpt5ClinDeptName,
        cs.Rpt6ClinDeptID,
        rcd6.RptClinDeptName AS Rpt6ClinDeptName,
        cs.DoctorID,
        d.DoctorName,
        cs.TimeSlotID,
        ts.TimeSlotName,
        cs.Room,
        cs.DayOfWeek,
        cs.WeekPattern,
        cs.StartDate,
        cs.EndDate,
        cs.Rpt1DisplayDoctorName,
        cs.ActiveFlag
    FROM T_ConsultationSlot cs
    LEFT JOIN M_ClinicalDepartment cd ON cd.ClinDeptID = cs.Rpt1ClinDeptID
    LEFT JOIN M_Specialty sp ON sp.SpecialtyID = cs.Rpt1SpecialtyID
    LEFT JOIN M_ReportClinicalDepartment rcd2 ON rcd2.RptClinDeptID = cs.Rpt2ClinDeptID
    LEFT JOIN M_ReportClinicalDepartment rcd3 ON rcd3.RptClinDeptID = cs.Rpt3ClinDeptID
    LEFT JOIN M_ReportClinicalDepartment rcd4 ON rcd4.RptClinDeptID = cs.Rpt4ClinDeptID
    LEFT JOIN M_ReportClinicalDepartment rcd5 ON rcd5.RptClinDeptID = cs.Rpt5ClinDeptID
    LEFT JOIN M_ReportClinicalDepartment rcd6 ON rcd6.RptClinDeptID = cs.Rpt6ClinDeptID
    LEFT JOIN M_Doctor d ON d.DoctorID = cs.DoctorID
    LEFT JOIN M_TimeSlot ts ON ts.TimeSlotID = cs.TimeSlotID
    ORDER BY cs.SlotID DESC
    LIMIT 500
    """,
    conn,
)

master_doctor = pd.read_sql(
    "SELECT DoctorID, DoctorName, Department, EmploymentType FROM M_Doctor ORDER BY DoctorID",
    conn,
)
master_dept = pd.read_sql(
    "SELECT ClinDeptID, ClinDeptName FROM M_ClinicalDepartment WHERE ActiveFlag = 1 ORDER BY ClinDeptID",
    conn,
)
master_timeslot = pd.read_sql(
    "SELECT TimeSlotID, TimeSlotName FROM M_TimeSlot ORDER BY TimeSlotID",
    conn,
)
master_specialty = pd.read_sql(
    "SELECT SpecialtyID, SpecialtyName FROM M_Specialty WHERE ActiveFlag = 1 ORDER BY SpecialtyID",
    conn,
)
master_report_dept = pd.read_sql(
    "SELECT RptClinDeptID, RptClinDeptName FROM M_ReportClinicalDepartment WHERE ActiveFlag = 1 ORDER BY RptClinDeptID",
    conn,
)

st.subheader("既存枠の検索・編集")
filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    dept_filter_options = [None] + master_dept["ClinDeptID"].astype(int).tolist()
    dept_filter = st.selectbox(
        "診療科フィルタ",
        dept_filter_options,
        format_func=lambda x: "(全て)" if x is None else f"{x}: {master_dept.loc[master_dept['ClinDeptID'] == x, 'ClinDeptName'].iloc[0]}",
    )
with filter_col2:
    doctor_filter_options = [None] + master_doctor["DoctorID"].astype(int).tolist()
    doctor_filter = st.selectbox(
        "医師フィルタ",
        doctor_filter_options,
        format_func=lambda x: "(全て)" if x is None else f"{x}: {master_doctor.loc[master_doctor['DoctorID'] == x, 'DoctorName'].iloc[0]}",
    )
with filter_col3:
    day_filter = st.selectbox("曜日フィルタ", ["(全て)"] + [label for _, label in DAY_OPTIONS])

view_df = slot_df.copy()
if dept_filter is not None:
    view_df = view_df[view_df["Rpt1ClinDeptID"] == dept_filter]
if doctor_filter is not None:
    view_df = view_df[view_df["DoctorID"] == doctor_filter]
if day_filter != "(全て)":
    day_num = next((v for v, l in DAY_OPTIONS if l == day_filter), None)
    view_df = view_df[view_df["DayOfWeek"] == day_num]

show_df = view_df.copy()
show_df["DayOfWeek"] = show_df["DayOfWeek"].apply(_day_label)
st.dataframe(show_df, use_container_width=True)

if view_df.empty:
    st.info("条件に合う枠がありません。")
else:
    slot_choices = view_df["SlotID"].astype(int).tolist()
    selected_slot_id = st.selectbox("編集対象SlotID", slot_choices)
    selected_row = view_df.loc[view_df["SlotID"] == selected_slot_id].iloc[0]

    st.caption("選択した枠を編集できます（終了日だけ修正したい場合も可）。")
    with st.form("edit_slot_form"):
        dept_options = [None] + master_dept["ClinDeptID"].astype(int).tolist()
        edit_dept_id = st.selectbox(
            "診療科",
            dept_options,
            index=_safe_option_index(dept_options, None if pd.isna(selected_row["Rpt1ClinDeptID"]) else int(selected_row["Rpt1ClinDeptID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_dept.loc[master_dept['ClinDeptID'] == x, 'ClinDeptName'].iloc[0]}",
        )
        doctor_options = [None] + master_doctor["DoctorID"].astype(int).tolist()
        edit_doctor_id = st.selectbox(
            "医師",
            doctor_options,
            index=_safe_option_index(doctor_options, None if pd.isna(selected_row["DoctorID"]) else int(selected_row["DoctorID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_doctor.loc[master_doctor['DoctorID'] == x, 'DoctorName'].iloc[0]}",
        )
        timeslot_options = [None] + master_timeslot["TimeSlotID"].astype(int).tolist()
        edit_timeslot_id = st.selectbox(
            "時間帯",
            timeslot_options,
            index=_safe_option_index(timeslot_options, None if pd.isna(selected_row["TimeSlotID"]) else int(selected_row["TimeSlotID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_timeslot.loc[master_timeslot['TimeSlotID'] == x, 'TimeSlotName'].iloc[0]}",
        )
        specialty_options = [None] + master_specialty["SpecialtyID"].astype(int).tolist()
        edit_specialty_id = st.selectbox(
            "専門外来名（Rpt1SpecialtyID）",
            specialty_options,
            index=_safe_option_index(specialty_options, None if pd.isna(selected_row["Rpt1SpecialtyID"]) else int(selected_row["Rpt1SpecialtyID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_specialty.loc[master_specialty['SpecialtyID'] == x, 'SpecialtyName'].iloc[0]}",
        )
        rpt_dept_options = [None] + master_report_dept["RptClinDeptID"].astype(int).tolist()
        edit_rpt2_dept_id = st.selectbox(
            "帳票➁用診療科名（Rpt2ClinDeptID）",
            rpt_dept_options,
            index=_safe_option_index(rpt_dept_options, None if pd.isna(selected_row["Rpt2ClinDeptID"]) else int(selected_row["Rpt2ClinDeptID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
        )
        edit_rpt3_dept_id = st.selectbox(
            "帳票➂用診療科名（Rpt3ClinDeptID）",
            rpt_dept_options,
            index=_safe_option_index(rpt_dept_options, None if pd.isna(selected_row["Rpt3ClinDeptID"]) else int(selected_row["Rpt3ClinDeptID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
        )
        edit_rpt4_dept_id = st.selectbox(
            "帳票➃用診療科名（Rpt4ClinDeptID）",
            rpt_dept_options,
            index=_safe_option_index(rpt_dept_options, None if pd.isna(selected_row["Rpt4ClinDeptID"]) else int(selected_row["Rpt4ClinDeptID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
        )
        edit_rpt5_dept_id = st.selectbox(
            "帳票➄用診療科名（Rpt5ClinDeptID）",
            rpt_dept_options,
            index=_safe_option_index(rpt_dept_options, None if pd.isna(selected_row["Rpt5ClinDeptID"]) else int(selected_row["Rpt5ClinDeptID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
        )
        edit_rpt6_dept_id = st.selectbox(
            "帳票⑥用診療科名（Rpt6ClinDeptID）",
            rpt_dept_options,
            index=_safe_option_index(rpt_dept_options, None if pd.isna(selected_row["Rpt6ClinDeptID"]) else int(selected_row["Rpt6ClinDeptID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
        )

        edit_room = st.text_input("診察室", value="" if pd.isna(selected_row["Room"]) else str(selected_row["Room"]))
        edit_day = st.selectbox(
            "曜日",
            [None] + [v for v, _ in DAY_OPTIONS],
            index=_safe_option_index([None] + [v for v, _ in DAY_OPTIONS], None if pd.isna(selected_row["DayOfWeek"]) or str(selected_row["DayOfWeek"]).strip() == "" else _safe_day_of_week(selected_row["DayOfWeek"])),
            format_func=lambda x: "未設定" if x is None else _day_label(x),
        )
        edit_weekpattern = st.text_input(
            "WeekPattern", value="" if pd.isna(selected_row["WeekPattern"]) else str(selected_row["WeekPattern"])
        )

        edit_start_value = _safe_date_for_widget(_safe_date_value(selected_row["StartDate"], fallback=date.today()))
        edit_start = st.date_input(
            "開始日",
            value=edit_start_value,
        )
        current_end_date = _safe_date_value(selected_row["EndDate"], fallback=DB_OPEN_END_DATE)
        edit_open_end = st.checkbox(
            "終了日未定（DB保存値: 9999-12-31）",
            value=current_end_date >= DB_OPEN_END_DATE,
            key=f"edit_open_end_{int(selected_slot_id)}",
        )
        edit_end_widget_value = (
            edit_start_value if current_end_date >= DB_OPEN_END_DATE else _safe_date_for_widget(current_end_date)
        )
        edit_end = st.date_input(
            "終了日",
            value=edit_end_widget_value,
        )
        if edit_open_end:
            st.caption("※ チェック時は入力値に関わらず 9999-12-31 で保存されます。")
        edit_display_name = st.text_input(
            "帳票①表示名（任意）",
            value="" if pd.isna(selected_row["Rpt1DisplayDoctorName"]) else str(selected_row["Rpt1DisplayDoctorName"]),
        )

        edit_active = st.checkbox("有効", value=int(selected_row["ActiveFlag"]) == 1)
        submitted_update = st.form_submit_button("更新")

        if submitted_update:
            conn.execute(
                """
                UPDATE T_ConsultationSlot
                SET
                    Rpt1ClinDeptID = ?,
                    Rpt1SpecialtyID = ?,
                    Rpt2ClinDeptID = ?,
                    Rpt3ClinDeptID = ?,
                    Rpt4ClinDeptID = ?,
                    Rpt5ClinDeptID = ?,
                    Rpt6ClinDeptID = ?,
                    DoctorID = ?,
                    TimeSlotID = ?,
                    Room = ?,
                    DayOfWeek = ?,
                    WeekPattern = ?,
                    StartDate = ?,
                    EndDate = ?,
                    Rpt1DisplayDoctorName = ?,
                    ActiveFlag = ?
                WHERE SlotID = ?
                """,
                (
                    edit_dept_id if edit_dept_id is None else int(edit_dept_id),
                    edit_specialty_id if edit_specialty_id is None else int(edit_specialty_id),
                    edit_rpt2_dept_id if edit_rpt2_dept_id is None else int(edit_rpt2_dept_id),
                    edit_rpt3_dept_id if edit_rpt3_dept_id is None else int(edit_rpt3_dept_id),
                    edit_rpt4_dept_id if edit_rpt4_dept_id is None else int(edit_rpt4_dept_id),
                    edit_rpt5_dept_id if edit_rpt5_dept_id is None else int(edit_rpt5_dept_id),
                    edit_rpt6_dept_id if edit_rpt6_dept_id is None else int(edit_rpt6_dept_id),
                    edit_doctor_id if edit_doctor_id is None else int(edit_doctor_id),
                    edit_timeslot_id if edit_timeslot_id is None else int(edit_timeslot_id),
                    edit_room if edit_room != "" else None,
                    edit_day if edit_day is None else int(edit_day),
                    edit_weekpattern,
                    str(edit_start),
                    "9999-12-31" if edit_open_end else str(edit_end),
                    edit_display_name if edit_display_name != "" else None,
                    1 if edit_active else 0,
                    int(selected_slot_id),
                ),
            )
            conn.commit()
            st.success("枠を更新しました。画面を再読み込みすると一覧に反映されます。")

st.divider()
st.subheader("新規枠追加（検索選択式）")

use_selected_as_default = st.checkbox("編集対象の枠を初期値としてコピーする", value=False)
default_row = selected_row if (use_selected_as_default and not view_df.empty) else None

with st.form("create_slot_form"):
    default_dept = int(default_row["Rpt1ClinDeptID"]) if default_row is not None and not pd.isna(default_row["Rpt1ClinDeptID"]) else None
    default_specialty = int(default_row["Rpt1SpecialtyID"]) if default_row is not None and not pd.isna(default_row["Rpt1SpecialtyID"]) else None
    default_rpt2_dept = int(default_row["Rpt2ClinDeptID"]) if default_row is not None and not pd.isna(default_row["Rpt2ClinDeptID"]) else None
    default_rpt3_dept = int(default_row["Rpt3ClinDeptID"]) if default_row is not None and not pd.isna(default_row["Rpt3ClinDeptID"]) else None
    default_rpt4_dept = int(default_row["Rpt4ClinDeptID"]) if default_row is not None and not pd.isna(default_row["Rpt4ClinDeptID"]) else None
    default_rpt5_dept = int(default_row["Rpt5ClinDeptID"]) if default_row is not None and not pd.isna(default_row["Rpt5ClinDeptID"]) else None
    default_rpt6_dept = int(default_row["Rpt6ClinDeptID"]) if default_row is not None and not pd.isna(default_row["Rpt6ClinDeptID"]) else None
    default_doctor = int(default_row["DoctorID"]) if default_row is not None and not pd.isna(default_row["DoctorID"]) else None
    default_timeslot = int(default_row["TimeSlotID"]) if default_row is not None and not pd.isna(default_row["TimeSlotID"]) else None

    new_dept_options = [None] + master_dept["ClinDeptID"].astype(int).tolist()
    new_dept_id = st.selectbox(
        "診療科",
        new_dept_options,
        index=_safe_option_index(new_dept_options, default_dept),
        format_func=lambda x: "未設定" if x is None else f"{x}: {master_dept.loc[master_dept['ClinDeptID'] == x, 'ClinDeptName'].iloc[0]}",
    )

    new_doctor_options = [None] + master_doctor["DoctorID"].astype(int).tolist()
    new_doctor_id = st.selectbox(
        "医師",
        new_doctor_options,
        index=_safe_option_index(new_doctor_options, default_doctor),
        format_func=lambda x: "未設定" if x is None else f"{x}: {master_doctor.loc[master_doctor['DoctorID'] == x, 'DoctorName'].iloc[0]}",
    )
with filter_col3:
    day_filter = st.selectbox("曜日フィルタ", ["(全て)"] + [label for _, label in DAY_OPTIONS])

view_df = slot_df.copy()
if dept_filter is not None:
    view_df = view_df[view_df["Rpt1ClinDeptID"] == dept_filter]
if doctor_filter is not None:
    view_df = view_df[view_df["DoctorID"] == doctor_filter]
if day_filter != "(全て)":
    day_num = next((v for v, l in DAY_OPTIONS if l == day_filter), None)
    view_df = view_df[view_df["DayOfWeek"] == day_num]

show_df = view_df.copy()
show_df["DayOfWeek"] = show_df["DayOfWeek"].apply(_day_label)
st.dataframe(show_df, use_container_width=True)

if view_df.empty:
    st.info("条件に合う枠がありません。")
else:
    slot_choices = view_df["SlotID"].astype(int).tolist()
    selected_slot_id = st.selectbox("編集対象SlotID", slot_choices)
    selected_row = view_df.loc[view_df["SlotID"] == selected_slot_id].iloc[0]

    st.caption("選択した枠を編集できます（終了日だけ修正したい場合も可）。")
    with st.form("edit_slot_form"):
        dept_options = [None] + master_dept["ClinDeptID"].astype(int).tolist()
        edit_dept_id = st.selectbox(
            "診療科",
            dept_options,
            index=_safe_option_index(dept_options, None if pd.isna(selected_row["Rpt1ClinDeptID"]) else int(selected_row["Rpt1ClinDeptID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_dept.loc[master_dept['ClinDeptID'] == x, 'ClinDeptName'].iloc[0]}",
        )
        doctor_options = [None] + master_doctor["DoctorID"].astype(int).tolist()
        edit_doctor_id = st.selectbox(
            "医師",
            doctor_options,
            index=_safe_option_index(doctor_options, None if pd.isna(selected_row["DoctorID"]) else int(selected_row["DoctorID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_doctor.loc[master_doctor['DoctorID'] == x, 'DoctorName'].iloc[0]}",
        )
        timeslot_options = [None] + master_timeslot["TimeSlotID"].astype(int).tolist()
        edit_timeslot_id = st.selectbox(
            "時間帯",
            timeslot_options,
            index=_safe_option_index(timeslot_options, None if pd.isna(selected_row["TimeSlotID"]) else int(selected_row["TimeSlotID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_timeslot.loc[master_timeslot['TimeSlotID'] == x, 'TimeSlotName'].iloc[0]}",
        )
        specialty_options = [None] + master_specialty["SpecialtyID"].astype(int).tolist()
        edit_specialty_id = st.selectbox(
            "専門外来名（Rpt1SpecialtyID）",
            specialty_options,
            index=_safe_option_index(specialty_options, None if pd.isna(selected_row["Rpt1SpecialtyID"]) else int(selected_row["Rpt1SpecialtyID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_specialty.loc[master_specialty['SpecialtyID'] == x, 'SpecialtyName'].iloc[0]}",
        )
        rpt_dept_options = [None] + master_report_dept["RptClinDeptID"].astype(int).tolist()
        edit_rpt2_dept_id = st.selectbox(
            "帳票➁用診療科名（Rpt2ClinDeptID）",
            rpt_dept_options,
            index=_safe_option_index(rpt_dept_options, None if pd.isna(selected_row["Rpt2ClinDeptID"]) else int(selected_row["Rpt2ClinDeptID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
        )
        edit_rpt3_dept_id = st.selectbox(
            "帳票➂用診療科名（Rpt3ClinDeptID）",
            rpt_dept_options,
            index=_safe_option_index(rpt_dept_options, None if pd.isna(selected_row["Rpt3ClinDeptID"]) else int(selected_row["Rpt3ClinDeptID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
        )
        edit_rpt4_dept_id = st.selectbox(
            "帳票➃用診療科名（Rpt4ClinDeptID）",
            rpt_dept_options,
            index=_safe_option_index(rpt_dept_options, None if pd.isna(selected_row["Rpt4ClinDeptID"]) else int(selected_row["Rpt4ClinDeptID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
        )
        edit_rpt5_dept_id = st.selectbox(
            "帳票➄用診療科名（Rpt5ClinDeptID）",
            rpt_dept_options,
            index=_safe_option_index(rpt_dept_options, None if pd.isna(selected_row["Rpt5ClinDeptID"]) else int(selected_row["Rpt5ClinDeptID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
        )
        edit_rpt6_dept_id = st.selectbox(
            "帳票⑥用診療科名（Rpt6ClinDeptID）",
            rpt_dept_options,
            index=_safe_option_index(rpt_dept_options, None if pd.isna(selected_row["Rpt6ClinDeptID"]) else int(selected_row["Rpt6ClinDeptID"])),
            format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
        )

        edit_room = st.text_input("診察室", value="" if pd.isna(selected_row["Room"]) else str(selected_row["Room"]))
        edit_day = st.selectbox(
            "曜日",
            [None] + [v for v, _ in DAY_OPTIONS],
            index=_safe_option_index([None] + [v for v, _ in DAY_OPTIONS], None if pd.isna(selected_row["DayOfWeek"]) or str(selected_row["DayOfWeek"]).strip() == "" else _safe_day_of_week(selected_row["DayOfWeek"])),
            format_func=lambda x: "未設定" if x is None else _day_label(x),
        )
        edit_weekpattern = st.text_input(
            "WeekPattern", value="" if pd.isna(selected_row["WeekPattern"]) else str(selected_row["WeekPattern"])
        )

        edit_start_value = _safe_date_for_widget(_safe_date_value(selected_row["StartDate"], fallback=date.today()))
        edit_start = st.date_input(
            "開始日",
            value=edit_start_value,
        )
        current_end_date = _safe_date_value(selected_row["EndDate"], fallback=DB_OPEN_END_DATE)
        edit_open_end = st.checkbox(
            "終了日未定（DB保存値: 9999-12-31）",
            value=current_end_date >= DB_OPEN_END_DATE,
            key=f"edit_open_end_{int(selected_slot_id)}",
        )
        edit_end_widget_value = (
            edit_start_value if current_end_date >= DB_OPEN_END_DATE else _safe_date_for_widget(current_end_date)
        )
        edit_end = st.date_input(
            "終了日",
            value=edit_end_widget_value,
        )
        if edit_open_end:
            st.caption("※ チェック時は入力値に関わらず 9999-12-31 で保存されます。")
        edit_display_name = st.text_input(
            "帳票①表示名（任意）",
            value="" if pd.isna(selected_row["Rpt1DisplayDoctorName"]) else str(selected_row["Rpt1DisplayDoctorName"]),
        )

        edit_active = st.checkbox("有効", value=int(selected_row["ActiveFlag"]) == 1)
        submitted_update = st.form_submit_button("更新")

    new_timeslot_options = [None] + master_timeslot["TimeSlotID"].astype(int).tolist()
    new_timeslot_id = st.selectbox(
        "時間帯",
        new_timeslot_options,
        index=_safe_option_index(new_timeslot_options, default_timeslot),
        format_func=lambda x: "未設定" if x is None else f"{x}: {master_timeslot.loc[master_timeslot['TimeSlotID'] == x, 'TimeSlotName'].iloc[0]}",
    )
    new_specialty_options = [None] + master_specialty["SpecialtyID"].astype(int).tolist()
    new_specialty_id = st.selectbox(
        "専門外来名（Rpt1SpecialtyID）",
        new_specialty_options,
        index=_safe_option_index(new_specialty_options, default_specialty),
        format_func=lambda x: "未設定" if x is None else f"{x}: {master_specialty.loc[master_specialty['SpecialtyID'] == x, 'SpecialtyName'].iloc[0]}",
    )
    new_rpt_dept_options = [None] + master_report_dept["RptClinDeptID"].astype(int).tolist()
    new_rpt2_dept_id = st.selectbox(
        "帳票➁用診療科名（Rpt2ClinDeptID）",
        new_rpt_dept_options,
        index=_safe_option_index(new_rpt_dept_options, default_rpt2_dept),
        format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
    )
    new_rpt3_dept_id = st.selectbox(
        "帳票➂用診療科名（Rpt3ClinDeptID）",
        new_rpt_dept_options,
        index=_safe_option_index(new_rpt_dept_options, default_rpt3_dept),
        format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
    )
    new_rpt4_dept_id = st.selectbox(
        "帳票➃用診療科名（Rpt4ClinDeptID）",
        new_rpt_dept_options,
        index=_safe_option_index(new_rpt_dept_options, default_rpt4_dept),
        format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
    )
    new_rpt5_dept_id = st.selectbox(
        "帳票➄用診療科名（Rpt5ClinDeptID）",
        new_rpt_dept_options,
        index=_safe_option_index(new_rpt_dept_options, default_rpt5_dept),
        format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
    )
    new_rpt6_dept_id = st.selectbox(
        "帳票⑥用診療科名（Rpt6ClinDeptID）",
        new_rpt_dept_options,
        index=_safe_option_index(new_rpt_dept_options, default_rpt6_dept),
        format_func=lambda x: "未設定" if x is None else f"{x}: {master_report_dept.loc[master_report_dept['RptClinDeptID'] == x, 'RptClinDeptName'].iloc[0]}",
    )

    new_room = st.text_input("診察室", value="" if default_row is None or pd.isna(default_row["Room"]) else str(default_row["Room"]))
    new_day = st.selectbox(
        "曜日",
        [None] + [v for v, _ in DAY_OPTIONS],
        index=_safe_option_index(
            [None] + [v for v, _ in DAY_OPTIONS],
            None if default_row is not None and (pd.isna(default_row["DayOfWeek"]) or str(default_row["DayOfWeek"]).strip() == "") else (_safe_day_of_week(default_row["DayOfWeek"]) if default_row is not None else 1),
            default=1,
        ),
        format_func=lambda x: "未設定" if x is None else _day_label(x),
    )
    new_weekpattern = st.text_input(
        "WeekPattern",
        value="12345" if default_row is None or pd.isna(default_row["WeekPattern"]) or str(default_row["WeekPattern"]).strip() == "" else str(default_row["WeekPattern"]),
    )
    new_start_value = _safe_date_for_widget(_safe_date_value(default_row["StartDate"], fallback=date.today())) if default_row is not None else date.today()
    new_start = st.date_input(
        "開始日",
        value=new_start_value,
        key="new_start_date",
    )
    default_new_end = _safe_date_value(default_row["EndDate"], fallback=DB_OPEN_END_DATE) if default_row is not None else DB_OPEN_END_DATE
    new_open_end = st.checkbox(
        "終了日未定（DB保存値: 9999-12-31）",
        value=default_new_end >= DB_OPEN_END_DATE,
        key="new_open_end_checkbox",
    )
    new_end_widget_value = (
        new_start_value if default_new_end >= DB_OPEN_END_DATE else _safe_date_for_widget(default_new_end)
    )
    new_end = st.date_input(
        "終了日",
        value=new_end_widget_value,
        key="new_end_date",
    )
    if new_open_end:
        st.caption("※ チェック時は入力値に関わらず 9999-12-31 で保存されます。")
    new_display_name = st.text_input(
        "帳票①表示名（任意）",
        value="" if default_row is None or pd.isna(default_row["Rpt1DisplayDoctorName"]) else str(default_row["Rpt1DisplayDoctorName"]),
    )

    submitted_create = st.form_submit_button("新規登録")
    if submitted_create:
        conn.execute(
            """
            INSERT INTO T_ConsultationSlot
            (
                Rpt1ClinDeptID,
                Rpt1SpecialtyID,
                Rpt2ClinDeptID,
                Rpt3ClinDeptID,
                Rpt4ClinDeptID,
                Rpt5ClinDeptID,
                Rpt6ClinDeptID,
                DoctorID,
                TimeSlotID,
                Room,
                DayOfWeek,
                WeekPattern,
                StartDate,
                EndDate,
                Rpt1DisplayDoctorName
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_dept_id if new_dept_id is None else int(new_dept_id),
                new_specialty_id if new_specialty_id is None else int(new_specialty_id),
                new_rpt2_dept_id if new_rpt2_dept_id is None else int(new_rpt2_dept_id),
                new_rpt3_dept_id if new_rpt3_dept_id is None else int(new_rpt3_dept_id),
                new_rpt4_dept_id if new_rpt4_dept_id is None else int(new_rpt4_dept_id),
                new_rpt5_dept_id if new_rpt5_dept_id is None else int(new_rpt5_dept_id),
                new_rpt6_dept_id if new_rpt6_dept_id is None else int(new_rpt6_dept_id),
                new_doctor_id if new_doctor_id is None else int(new_doctor_id),
                new_timeslot_id if new_timeslot_id is None else int(new_timeslot_id),
                new_room if new_room != "" else None,
                new_day if new_day is None else int(new_day),
                new_weekpattern,
                str(new_start),
                "9999-12-31" if new_open_end else str(new_end),
                new_display_name if new_display_name != "" else None,
            ),
        )
        conn.commit()
        st.success("新規枠を登録しました。")
