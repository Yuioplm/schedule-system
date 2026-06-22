from __future__ import annotations

from datetime import date
from io import BytesIO
import sqlite3

import pandas as pd
import pytest

openpyxl = pytest.importorskip("openpyxl")
load_workbook = openpyxl.load_workbook

from streamlit_app.report2_excel import (
    DIFF_NEW,
    DIFF_UNCHANGED,
    DIFF_UPDATED,
    add_diff_status,
    build_report2_excel,
    build_row_hash,
    save_official_output_history,
)


def _report_row(change_detail: str = "担当変更") -> dict[str, object]:
    return {
        "登録種別": "通常変更",
        "レコードID": 1,
        "差分キー": "change:2026-04-06:1",
        "日付": "2026-04-06",
        "曜日": "月",
        "時間": "午前",
        "診療科名": "内科",
        "変更前医師": "医師A",
        "変更内容": change_detail,
        "備考": "備考",
    }


def test_add_diff_status_classifies_new_updated_and_unchanged() -> None:
    old_df = pd.DataFrame([_report_row("担当変更")])
    old_hash = build_row_hash(old_df.iloc[0])

    unchanged_df = add_diff_status(old_df, {"change:2026-04-06:1": old_hash})
    assert unchanged_df.iloc[0]["差分区分"] == DIFF_UNCHANGED

    updated_df = pd.DataFrame([_report_row("担当変更（更新）")])
    updated_df = add_diff_status(updated_df, {"change:2026-04-06:1": old_hash})
    assert updated_df.iloc[0]["差分区分"] == DIFF_UPDATED

    new_df = add_diff_status(old_df, {})
    assert new_df.iloc[0]["差分区分"] == DIFF_NEW


def test_build_report2_excel_outputs_workbook() -> None:
    df = add_diff_status(pd.DataFrame([_report_row("休診 要確認")]), {})

    workbook_bytes = build_report2_excel(df, "確認用")

    workbook = load_workbook(BytesIO(workbook_bytes))
    sheet = workbook.active
    assert sheet.title == "帳票②予定変更一覧"
    assert sheet["A1"].value == "帳票② 予定変更一覧（確認用）"
    assert sheet["A3"].value == DIFF_NEW


def test_save_official_output_history_persists_snapshot() -> None:
    conn = sqlite3.connect(":memory:")
    try:
        df = add_diff_status(pd.DataFrame([_report_row()]), {})

        history_id = save_official_output_history(
            conn,
            df,
            start_date=date(2026, 4, 1),
            output_by="tester",
            output_date=date(2026, 6, 22),
            file_name="report.xlsx",
        )

        history = conn.execute("SELECT OutputBy, RecordCount FROM T_Report2OutputHistory").fetchone()
        detail = conn.execute(
            "SELECT OutputHistoryID, DiffKey FROM T_Report2OutputHistoryDetail"
        ).fetchone()
        assert history == ("tester", 1)
        assert detail == (history_id, "change:2026-04-06:1")
    finally:
        conn.close()
