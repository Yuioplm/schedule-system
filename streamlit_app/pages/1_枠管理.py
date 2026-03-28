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


st.title("枠管理")
conn = get_conn()

slot_df = pd.read_sql(
    """
    SELECT
        cs.SlotID,
        cs.Rpt1ClinDeptID,
        cd.ClinDeptName,
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
    LEFT JOIN M_Doctor d ON d.DoctorID = cs.DoctorID
    LEFT JOIN M_TimeSlot ts ON ts.TimeSlotID = cs.TimeSlotID
    ORDER BY cs.SlotID DESC
    LIMIT 500
    """,
    conn,
)

master_doctor = pd.read_sql(
    "SELECT DoctorID, DoctorName, Department, EmploymentType FROM M_Doctor ORDER BY Department, EmploymentType, DoctorName",
    conn,
)
master_dept = pd.read_sql(
    "SELECT ClinDeptID, ClinDeptName FROM M_ClinicalDepartment WHERE ActiveFlag = 1 ORDER BY Rpt1Sort, ClinDeptID",
    conn,
)
master_timeslot = pd.read_sql(
    "SELECT TimeSlotID, TimeSlotName FROM M_TimeSlot ORDER BY TimeSlotID",
    conn,
)

st.subheader("既存枠の検索・編集")
filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    dept_filter = st.selectbox(
        "診療科フィルタ",
        ["(全て)"] + master_dept["ClinDeptName"].dropna().unique().tolist(),
    )
with filter_col2:
    doctor_filter = st.selectbox(
        "医師フィルタ",
        ["(全て)"] + master_doctor["DoctorName"].dropna().unique().tolist(),
    )
with filter_col3:
    day_filter = st.selectbox("曜日フィルタ", ["(全て)"] + [label for _, label in DAY_OPTIONS])

view_df = slot_df.copy()
if dept_filter != "(全て)":
    view_df = view_df[view_df["ClinDeptName"] == dept_filter]
if doctor_filter != "(全て)":
    view_df = view_df[view_df["DoctorName"] == doctor_filter]
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
        edit_dept_id = st.selectbox(
            "診療科",
            master_dept["ClinDeptID"].astype(int).tolist(),
            index=_safe_index(master_dept, "ClinDeptID", selected_row["Rpt1ClinDeptID"]),
            format_func=lambda x: f"{x}: {master_dept.loc[master_dept['ClinDeptID'] == x, 'ClinDeptName'].iloc[0]}",
        )
        edit_doctor_id = st.selectbox(
            "医師",
            master_doctor["DoctorID"].astype(int).tolist(),
            index=_safe_index(master_doctor, "DoctorID", selected_row["DoctorID"]),
            format_func=lambda x: f"{x}: {master_doctor.loc[master_doctor['DoctorID'] == x, 'DoctorName'].iloc[0]}",
        )
        edit_timeslot_id = st.selectbox(
            "時間帯",
            master_timeslot["TimeSlotID"].astype(int).tolist(),
            index=_safe_index(master_timeslot, "TimeSlotID", selected_row["TimeSlotID"]),
            format_func=lambda x: f"{x}: {master_timeslot.loc[master_timeslot['TimeSlotID'] == x, 'TimeSlotName'].iloc[0]}",
        )

        edit_room = st.text_input("診察室", value="" if pd.isna(selected_row["Room"]) else str(selected_row["Room"]))
        edit_day = st.selectbox(
            "曜日",
            [v for v, _ in DAY_OPTIONS],
            index=[v for v, _ in DAY_OPTIONS].index(int(selected_row["DayOfWeek"])),
            format_func=lambda x: _day_label(x),
        )
        edit_weekpattern = st.text_input(
            "WeekPattern", value="" if pd.isna(selected_row["WeekPattern"]) else str(selected_row["WeekPattern"])
        )

        edit_start = st.date_input(
            "開始日",
            value=_safe_date_for_widget(_safe_date_value(selected_row["StartDate"], fallback=date.today())),
        )
        current_end_date = _safe_date_value(selected_row["EndDate"], fallback=DB_OPEN_END_DATE)
        edit_open_end = st.checkbox(
            "終了日未定（DB保存値: 9999-12-31）",
            value=current_end_date >= DB_OPEN_END_DATE,
            key=f"edit_open_end_{int(selected_slot_id)}",
        )
        edit_end = st.date_input(
            "終了日",
            value=_safe_date_for_widget(current_end_date),
            disabled=edit_open_end,
        )
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
                    int(edit_dept_id),
                    int(edit_doctor_id),
                    int(edit_timeslot_id),
                    edit_room if edit_room != "" else None,
                    int(edit_day),
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
    default_dept = int(default_row["Rpt1ClinDeptID"]) if default_row is not None and not pd.isna(default_row["Rpt1ClinDeptID"]) else int(master_dept["ClinDeptID"].iloc[0])
    default_doctor = int(default_row["DoctorID"]) if default_row is not None and not pd.isna(default_row["DoctorID"]) else int(master_doctor["DoctorID"].iloc[0])
    default_timeslot = int(default_row["TimeSlotID"]) if default_row is not None and not pd.isna(default_row["TimeSlotID"]) else int(master_timeslot["TimeSlotID"].iloc[0])

    new_dept_id = st.selectbox(
        "診療科",
        master_dept["ClinDeptID"].astype(int).tolist(),
        index=_safe_index(master_dept, "ClinDeptID", default_dept),
        format_func=lambda x: f"{x}: {master_dept.loc[master_dept['ClinDeptID'] == x, 'ClinDeptName'].iloc[0]}",
    )

    new_doctor_id = st.selectbox(
        "医師",
        master_doctor["DoctorID"].astype(int).tolist(),
        index=_safe_index(master_doctor, "DoctorID", default_doctor),
        format_func=lambda x: f"{x}: {master_doctor.loc[master_doctor['DoctorID'] == x, 'DoctorName'].iloc[0]}",
    )

    new_timeslot_id = st.selectbox(
        "時間帯",
        master_timeslot["TimeSlotID"].astype(int).tolist(),
        index=_safe_index(master_timeslot, "TimeSlotID", default_timeslot),
        format_func=lambda x: f"{x}: {master_timeslot.loc[master_timeslot['TimeSlotID'] == x, 'TimeSlotName'].iloc[0]}",
    )

    new_room = st.text_input("診察室", value="" if default_row is None or pd.isna(default_row["Room"]) else str(default_row["Room"]))
    new_day = st.selectbox(
        "曜日",
        [v for v, _ in DAY_OPTIONS],
        index=[v for v, _ in DAY_OPTIONS].index(int(default_row["DayOfWeek"])) if default_row is not None else 1,
        format_func=lambda x: _day_label(x),
    )
    new_weekpattern = st.text_input(
        "WeekPattern",
        value="11111" if default_row is None or pd.isna(default_row["WeekPattern"]) else str(default_row["WeekPattern"]),
    )
    new_start = st.date_input(
        "開始日",
        value=_safe_date_for_widget(_safe_date_value(default_row["StartDate"], fallback=date.today())) if default_row is not None else date.today(),
        key="new_start_date",
    )
    default_new_end = _safe_date_value(default_row["EndDate"], fallback=DB_OPEN_END_DATE) if default_row is not None else DB_OPEN_END_DATE
    new_open_end = st.checkbox(
        "終了日未定（DB保存値: 9999-12-31）",
        value=default_new_end >= DB_OPEN_END_DATE,
        key="new_open_end_checkbox",
    )
    new_end = st.date_input(
        "終了日",
        value=_safe_date_for_widget(default_new_end) if default_row is not None else STREAMLIT_MAX_DATE,
        disabled=new_open_end,
        key="new_end_date",
    )
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
                DoctorID,
                TimeSlotID,
                Room,
                DayOfWeek,
                WeekPattern,
                StartDate,
                EndDate,
                Rpt1DisplayDoctorName
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(new_dept_id),
                int(new_doctor_id),
                int(new_timeslot_id),
                new_room if new_room != "" else None,
                int(new_day),
                new_weekpattern,
                str(new_start),
                "9999-12-31" if new_open_end else str(new_end),
                new_display_name if new_display_name != "" else None,
            ),
        )
        conn.commit()
        st.success("新規枠を登録しました。")
