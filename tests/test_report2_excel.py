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


def _report_row(change_detail: str = "担当変更", reason: str = "備考") -> dict[str, object]:
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
        "備考": reason,
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
    df = add_diff_status(pd.DataFrame([_report_row("休診", "取消")]), {})

    workbook_bytes = build_report2_excel(df, "プレビュー")

    workbook = load_workbook(BytesIO(workbook_bytes))
    sheet = workbook.active
    assert sheet.title == "帳票②予定変更一覧"
    assert sheet["A1"].value == "担当医師変更連絡表"
    assert sheet["A1"].font.bold is False
    assert sheet["A1"].font.sz == 24
    assert sheet["A2"].value is None
    assert sheet["A4"].value == "2026-04-06"
    assert sheet["A4"].fill.fgColor.rgb == "FF00FFFF"
    assert sheet["A4"].border.diagonalUp is True
    assert sheet["A4"].border.diagonal.style == "medium"
    assert sheet["A4"].border.diagonal.color.rgb == "00000000"
    assert sheet["F4"].border.diagonalUp is True
    assert sheet["F4"].border.diagonal.style == "medium"
    assert sheet["F4"].border.diagonal.color.rgb == "00000000"
    assert sheet["G4"].value == "取消"
    assert sheet["G4"].border.diagonalUp is False
    assert sheet["G4"].border.diagonalDown is False
    assert sheet["G4"].border.diagonal.style is None
    assert sheet.row_dimensions[4].height == 41.25
    assert sheet["A3"].alignment.shrink_to_fit is True
    assert sheet["A4"].alignment.shrink_to_fit is True
    assert sheet["A1"].alignment.shrink_to_fit is None
    assert sheet.page_setup.orientation == "portrait"
    assert sheet.page_setup.fitToWidth == 1
    assert sheet.page_setup.fitToHeight == 0
    assert sheet.page_margins.top == pytest.approx(1 / 2.54)
    assert sheet.page_margins.bottom == pytest.approx(1 / 2.54)
    assert sheet.page_margins.left == pytest.approx(0.3 / 2.54)
    assert sheet.page_margins.right == pytest.approx(0.3 / 2.54)
    assert sheet.page_margins.header == pytest.approx(1.9 / 2.54)
    assert sheet.page_margins.footer == pytest.approx(0.6 / 2.54)
    assert sheet.sheet_view.zoomScale == 55
    assert sheet.column_dimensions["A"].width == 28.33
    assert sheet.column_dimensions["G"].width == 109.33
    assert sheet.print_options.horizontalCentered is True
    assert sheet.print_title_rows == "$1:$3"


def test_build_report2_excel_highlights_only_change_detail_for_existing_rest_day() -> None:
    base_df = pd.DataFrame([_report_row("休診")])
    row_hash = build_row_hash(base_df.iloc[0])
    df = add_diff_status(base_df, {"change:2026-04-06:1": row_hash})

    workbook_bytes = build_report2_excel(df, "プレビュー")

    workbook = load_workbook(BytesIO(workbook_bytes))
    sheet = workbook.active
    assert sheet["A4"].fill.fill_type is None
    assert sheet["F4"].value == "休診"
    assert sheet["F4"].fill.fgColor.rgb == "FF00FFFF"


def test_build_report2_excel_does_not_diagonal_normalized_row() -> None:
    df = add_diff_status(pd.DataFrame([_report_row("休診→通常通り", "取消")]), {})

    workbook_bytes = build_report2_excel(df, "プレビュー")

    workbook = load_workbook(BytesIO(workbook_bytes))
    sheet = workbook.active
    assert sheet["A4"].value == "2026-04-06"
    assert sheet["A4"].fill.fgColor.rgb == "FF00FFFF"
    assert sheet["A4"].border.diagonalUp is False


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
