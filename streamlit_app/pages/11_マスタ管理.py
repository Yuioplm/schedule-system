import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from scripts.settings import get_conn


st.title("マスタ管理")
conn = get_conn()


MASTER_CONFIGS = [
    {
        "tab": "診療科",
        "table": "M_ClinicalDepartment",
        "pk": "ClinDeptID",
        "display": "ClinDeptName",
        "fields": [
            ("Category", "text"),
            ("ClinDeptName", "text"),
            ("Rpt1Sort", "int"),
            ("Rpt1Flag", "text"),
            ("Rpt2Flag", "text"),
            ("Rpt3Flag", "text"),
            ("Rpt4Flag", "text"),
            ("Rpt5Flag", "text"),
            ("Rpt6Flag", "text"),
            ("ActiveFlag", "bool"),
        ],
    },
    {
        "tab": "医師",
        "table": "M_Doctor",
        "pk": "DoctorID",
        "display": "DoctorName",
        "fields": [
            ("DoctorName", "text"),
            ("Department", "text"),
            ("EmploymentType", "text"),
            ("ActiveFlag", "bool"),
        ],
    },
    {
        "tab": "時間帯",
        "table": "M_TimeSlot",
        "pk": "TimeSlotID",
        "display": "TimeSlotName",
        "fields": [("TimeSlotName", "text")],
    },
    {
        "tab": "専門",
        "table": "M_Specialty",
        "pk": "SpecialtyID",
        "display": "SpecialtyName",
        "fields": [("SpecialtyName", "text"), ("ActiveFlag", "bool")],
    },
    {
        "tab": "帳票診療科",
        "table": "M_ReportClinicalDepartment",
        "pk": "RptClinDeptID",
        "display": "RptClinDeptName",
        "fields": [("RptClinDeptName", "text"), ("ActiveFlag", "bool")],
    },
    {
        "tab": "変更種別",
        "table": "M_ScheduleChangeType",
        "pk": "ChangeTypeID",
        "display": "ChangeTypeName",
        "fields": [
            ("ChangeTypeName", "text"),
            ("IsCancel", "bool"),
            ("ActiveFlag", "bool"),
        ],
    },
]


def _input_widget(field_name: str, field_type: str, default, key_prefix: str):
    key = f"{key_prefix}_{field_name}"
    if field_type == "int":
        val = 0 if default is None or pd.isna(default) else int(default)
        return st.number_input(field_name, value=val, step=1, key=key)
    if field_type == "bool":
        val = False if default is None or pd.isna(default) else int(default) == 1
        return 1 if st.checkbox(field_name, value=val, key=key) else 0
    val = "" if default is None or pd.isna(default) else str(default)
    return st.text_input(field_name, value=val, key=key)


def render_master_ui(config: dict):
    table = config["table"]
    pk = config["pk"]
    display = config["display"]
    fields = config["fields"]

    df = pd.read_sql(f"SELECT * FROM {table} ORDER BY {pk}", conn)
    st.caption(f"テーブル: {table}")

    keyword = st.text_input(
        "検索",
        value="",
        key=f"search_{table}",
        help=f"{display} に含まれる文字で絞り込み",
    )

    view_df = df.copy()
    if keyword.strip() != "" and display in view_df.columns:
        view_df = view_df[view_df[display].fillna("").str.contains(keyword, na=False)]

    st.dataframe(view_df, use_container_width=True)

    if view_df.empty:
        st.info("表示対象がありません。新規登録を利用してください。")
    else:
        options = view_df[pk].tolist()
        selected_id = st.selectbox(
            f"編集対象 {pk}",
            options,
            key=f"select_{table}",
            format_func=lambda x: f"{x}: {view_df.loc[view_df[pk] == x, display].iloc[0] if display in view_df.columns else x}",
        )

        row = view_df.loc[view_df[pk] == selected_id].iloc[0]
        with st.form(f"edit_form_{table}"):
            st.subheader("既存データ編集")
            values = {}
            for field_name, field_type in fields:
                values[field_name] = _input_widget(
                    field_name,
                    field_type,
                    row[field_name] if field_name in row else None,
                    f"edit_{table}_{selected_id}",
                )

            submitted = st.form_submit_button("更新")
            if submitted:
                set_clause = ", ".join([f"{k} = ?" for k in values.keys()])
                params = list(values.values()) + [selected_id]
                conn.execute(
                    f"UPDATE {table} SET {set_clause} WHERE {pk} = ?",
                    params,
                )
                conn.commit()
                st.success("更新しました。")

    with st.form(f"create_form_{table}"):
        st.subheader("新規登録")
        new_id = st.number_input(pk, step=1, value=0, key=f"new_pk_{table}")
        new_values = {}
        for field_name, field_type in fields:
            default = 1 if field_type == "bool" and field_name == "ActiveFlag" else None
            new_values[field_name] = _input_widget(
                field_name,
                field_type,
                default,
                f"new_{table}",
            )

        submitted_new = st.form_submit_button("登録")
        if submitted_new:
            columns = [pk] + list(new_values.keys())
            placeholders = ",".join(["?"] * len(columns))
            params = [int(new_id)] + list(new_values.values())
            conn.execute(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                params,
            )
            conn.commit()
            st.success("登録しました。")


master_tabs = st.tabs([cfg["tab"] for cfg in MASTER_CONFIGS])
for tab, cfg in zip(master_tabs, MASTER_CONFIGS):
    with tab:
        render_master_ui(cfg)
