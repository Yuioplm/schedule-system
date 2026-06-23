from datetime import date
from time import perf_counter

import pandas as pd
import streamlit as st

from scripts.settings import get_conn
from streamlit_app.log_events import log_event, log_page_open
from streamlit_app.page_support import render_page_guide
from streamlit_app.report2_excel import (
    DISPLAY_COLUMNS,
    add_diff_status,
    build_report2_excel,
    ensure_report2_output_tables,
    load_latest_official_snapshot,
    save_official_output_history,
)
from streamlit_app.sql_loader import load_sql

st.set_page_config(layout="wide")
st.title("帳票➁ 予定変更一覧")
log_page_open("帳票➁ 予定変更一覧")
render_page_guide("帳票➁ 予定変更一覧")

conn = get_conn()
ensure_report2_output_tables(conn)

start_date = st.date_input("検索開始日を選んでください")

query = load_sql("Report2.sql")
request_id = log_event(
    "report_generate_start",
    "帳票➁ 予定変更一覧",
    report_id="report2",
    start_date=str(start_date),
)
report_started_at = perf_counter()
try:
    df = pd.read_sql(query, conn, params={"start_date": str(start_date)})
except Exception as exc:
    log_event(
        "report_generate_failed",
        "帳票➁ 予定変更一覧",
        request_id=request_id,
        report_id="report2",
        error=type(exc).__name__,
    )
    raise

elapsed_ms = int((perf_counter() - report_started_at) * 1000)
log_event(
    "report_generate_success",
    "帳票➁ 予定変更一覧",
    request_id=request_id,
    report_id="report2",
    result_count=len(df),
    elapsed_ms=elapsed_ms,
)

if df.empty:
    st.warning("データがありません")
else:
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Excelダウンロード（CSV）",
        data=csv,
        file_name="帳票➁_予定変更一覧.csv",
        mime="text/csv",
    )

st.markdown("---")
st.subheader("書式付きExcel出力")
st.caption(
    "前回の配布用Excel出力履歴と今回の帳票②出力内容を比較し、"
    "新規・更新行を水色かつ太字で出力します。プレビュー出力は次回差分判定の基準にしません。"
)

export_query = load_sql("Report2_export.sql")
export_df = pd.read_sql(export_query, conn, params={"start_date": str(start_date)})
previous_snapshot = load_latest_official_snapshot(conn)
diff_df = add_diff_status(export_df, previous_snapshot)
preview_columns = ["差分区分", *DISPLAY_COLUMNS]

if diff_df.empty:
    st.warning("書式付きExcelの出力対象データがありません")
else:
    st.dataframe(diff_df[preview_columns], use_container_width=True)
    diff_counts = diff_df["差分区分"].value_counts().to_dict()
    st.caption(
        " / ".join(f"{key}: {value}件" for key, value in diff_counts.items())
    )

    trial_file_name = f"帳票②_予定変更一覧_プレビュー_{date.today():%Y%m%d}.xlsx"
    official_file_name = f"帳票②_予定変更一覧_配布用_{date.today():%Y%m%d}.xlsx"
    trial_excel = build_report2_excel(diff_df, "プレビュー")
    official_excel = build_report2_excel(diff_df, "配布用")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="プレビューExcelダウンロード（履歴に登録しない）",
            data=trial_excel,
            file_name=trial_file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col2:
        output_by = st.text_input("出力者（配布用・任意）", value="")
        official_clicked = st.download_button(
            label="配布用Excelダウンロード（履歴に登録）",
            data=official_excel,
            file_name=official_file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        if official_clicked:
            history_id = save_official_output_history(
                conn,
                diff_df,
                start_date=start_date,
                output_by=output_by,
                output_date=date.today(),
                file_name=official_file_name,
            )
            log_event(
                "report_generate_success",
                "帳票➁ 予定変更一覧",
                report_id="report2_template_official",
                result_count=len(diff_df),
                output_history_id=history_id,
            )
            st.success(f"配布用Excelの出力履歴を登録しました（履歴ID: {history_id}）。")

with st.expander("配布用Excel出力履歴"):
    history_df = pd.read_sql(
        """
        SELECT
            OutputHistoryID AS 履歴ID,
            StartDate AS 検索開始日,
            OutputBy AS 出力者,
            OutputDate AS 出力日,
            FileName AS ファイル名,
            RecordCount AS 件数,
            CreatedAt AS 登録日時
        FROM T_Report2OutputHistory
        WHERE OutputMode = 'official'
          AND OutputStatus = 'active'
        ORDER BY CreatedAt DESC, OutputHistoryID DESC
        LIMIT 20
        """,
        conn,
    )
    if history_df.empty:
        st.info("配布用Excel出力履歴はまだありません。")
    else:
        st.dataframe(history_df, use_container_width=True)
        cancel_target = st.selectbox(
            "取消する出力履歴ID",
            options=[None, *history_df["履歴ID"].tolist()],
            format_func=lambda value: "選択してください" if value is None else str(value),
        )
        cancel_reason = st.text_input("取消理由", value="")
        cancel_by = st.text_input("取消者（任意）", value="")
        if st.button("選択した出力履歴を取消"):
            if cancel_target is None:
                st.warning("取消する出力履歴IDを選択してください。")
            elif not cancel_reason.strip():
                st.warning("取消理由を入力してください。")
            else:
                conn.execute(
                    """
                    UPDATE T_Report2OutputHistory
                    SET OutputStatus = 'cancelled',
                        CancelledAt = datetime('now', '+9 hours'),
                        CancelledBy = ?,
                        CancelReason = ?
                    WHERE OutputHistoryID = ?
                      AND OutputMode = 'official'
                      AND OutputStatus = 'active'
                    """,
                    (cancel_by or None, cancel_reason, int(cancel_target)),
                )
                conn.commit()
                st.success("配布用Excel出力履歴を取消しました。再読み込み後、差分基準から除外されます。")
