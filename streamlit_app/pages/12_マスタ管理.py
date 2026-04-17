import streamlit as st
import pandas as pd
from time import perf_counter
import subprocess
import sys
from pathlib import Path

from scripts.settings import get_conn
from streamlit_app.log_events import log_event, log_page_open


st.title("マスタ管理")
log_page_open("マスタ管理")
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
                request_id = log_event(
                    "update_start",
                    "マスタ管理",
                    operation="update_master",
                    table=table,
                    target_id=selected_id,
                )
                update_started_at = perf_counter()
                set_clause = ", ".join([f"{k} = ?" for k in values.keys()])
                params = list(values.values()) + [selected_id]
                try:
                    conn.execute(
                        f"UPDATE {table} SET {set_clause} WHERE {pk} = ?",
                        params,
                    )
                    conn.commit()
                    elapsed_ms = int((perf_counter() - update_started_at) * 1000)
                    log_event(
                        "update_success",
                        "マスタ管理",
                        request_id=request_id,
                        operation="update_master",
                        table=table,
                        elapsed_ms=elapsed_ms,
                    )
                    st.success("更新しました。")
                except Exception as exc:
                    log_event(
                        "update_failed",
                        "マスタ管理",
                        request_id=request_id,
                        operation="update_master",
                        table=table,
                        error=type(exc).__name__,
                    )
                    raise

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
            request_id = log_event(
                "update_start",
                "マスタ管理",
                operation="insert_master",
                table=table,
                target_id=int(new_id),
            )
            update_started_at = perf_counter()
            columns = [pk] + list(new_values.keys())
            placeholders = ",".join(["?"] * len(columns))
            params = [int(new_id)] + list(new_values.values())
            try:
                conn.execute(
                    f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                    params,
                )
                conn.commit()
                elapsed_ms = int((perf_counter() - update_started_at) * 1000)
                log_event(
                    "update_success",
                    "マスタ管理",
                    request_id=request_id,
                    operation="insert_master",
                    table=table,
                    elapsed_ms=elapsed_ms,
                )
                st.success("登録しました。")
            except Exception as exc:
                log_event(
                    "update_failed",
                    "マスタ管理",
                    request_id=request_id,
                    operation="insert_master",
                    table=table,
                    error=type(exc).__name__,
                )
                raise


def get_fiscal_year_range() -> tuple[int | None, int | None]:
    row = conn.execute("""
        SELECT
            MIN(
                CASE
                    WHEN CAST(strftime('%m', CalendarDate) AS INTEGER) >= 4
                        THEN CAST(strftime('%Y', CalendarDate) AS INTEGER)
                    ELSE CAST(strftime('%Y', CalendarDate) AS INTEGER) - 1
                END
            ) AS min_fy,
            MAX(
                CASE
                    WHEN CAST(strftime('%m', CalendarDate) AS INTEGER) >= 4
                        THEN CAST(strftime('%Y', CalendarDate) AS INTEGER)
                    ELSE CAST(strftime('%Y', CalendarDate) AS INTEGER) - 1
                END
            ) AS max_fy
        FROM M_Date
    """).fetchone()
    return row[0], row[1]


def run_extend_fiscal_year(start_fy: int | None, end_fy: int | None) -> tuple[int, str, str]:
    cmd = [sys.executable, str(Path("scripts/extend_fiscal_year.py"))]
    if start_fy is not None:
        cmd.extend(["--start-fy", str(start_fy)])
    if end_fy is not None:
        cmd.extend(["--end-fy", str(end_fy)])

    completed = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def render_fiscal_year_admin_ui():
    st.subheader("年度管理")
    min_fy, max_fy = get_fiscal_year_range()
    if min_fy is None or max_fy is None:
        st.warning("M_Date が空のため、先に初期セットアップを実行してください。")
        return

    st.info(f"現在の登録範囲: {min_fy}年度 ～ {max_fy}年度")

    mode = st.radio(
        "追加方法",
        options=["次年度を1年追加", "年度範囲を指定して追加"],
        horizontal=False,
    )

    with st.form("extend_fiscal_year_form"):
        if mode == "次年度を1年追加":
            start_fy = None
            end_fy = None
            st.caption(f"次に追加される年度: {max_fy + 1}年度")
        else:
            start_fy = st.number_input("開始年度", min_value=2000, max_value=2100, value=max_fy + 1, step=1)
            end_fy = st.number_input("終了年度", min_value=2000, max_value=2100, value=max_fy + 1, step=1)

        submitted = st.form_submit_button("年度を追加")

        if submitted:
            request_id = log_event(
                "update_start",
                "マスタ管理",
                operation="extend_fiscal_year",
                start_fiscal_year=start_fy,
                end_fiscal_year=end_fy,
            )
            started_at = perf_counter()
            try:
                return_code, stdout, stderr = run_extend_fiscal_year(start_fy, end_fy)
                elapsed_ms = int((perf_counter() - started_at) * 1000)
                if return_code == 0:
                    log_event(
                        "update_success",
                        "マスタ管理",
                        request_id=request_id,
                        operation="extend_fiscal_year",
                        elapsed_ms=elapsed_ms,
                    )
                    st.success("年度追加が完了しました。画面を再読込すると最新状態を確認できます。")
                    if stdout.strip():
                        st.code(stdout)
                else:
                    log_event(
                        "update_failed",
                        "マスタ管理",
                        request_id=request_id,
                        operation="extend_fiscal_year",
                        elapsed_ms=elapsed_ms,
                        error=f"return_code={return_code}",
                    )
                    st.error("年度追加に失敗しました。")
                    if stderr.strip():
                        st.code(stderr)
            except Exception as exc:
                log_event(
                    "update_failed",
                    "マスタ管理",
                    request_id=request_id,
                    operation="extend_fiscal_year",
                    error=type(exc).__name__,
                )
                raise


tabs = st.tabs([cfg["tab"] for cfg in MASTER_CONFIGS] + ["年度管理"])
for tab, cfg in zip(tabs[:-1], MASTER_CONFIGS):
    with tab:
        render_master_ui(cfg)

with tabs[-1]:
    render_fiscal_year_admin_ui()
