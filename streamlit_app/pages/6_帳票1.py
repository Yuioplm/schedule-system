import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from io import BytesIO
import re

from openpyxl import load_workbook
from openpyxl.utils.cell import coordinate_to_tuple, range_boundaries, get_column_letter

from scripts.settings import get_conn

sys.path.append(str(Path(__file__).resolve().parents[2]))

from streamlit_app.sql_loader import load_sql


REPORT1_TEMPLATE_HEADER_CELL_MAP = {
    "year": "F1",
    "month": "G1",
}

REPORT1_TEMPLATE_ROW_START = 3
REPORT1_TEMPLATE_COLUMN_MAP = {
    "センター": "B",
    "診療科": "C",
    "時間": "D",
    "月": "E",
    "火": "F",
    "水": "G",
    "木": "H",
    "金": "I",
    "土": "J",
}


def build_report1_template_excel(
    df: pd.DataFrame,
    year: int,
    month: int,
    template_bytes: bytes,
) -> bytes:
    workbook = load_workbook(BytesIO(template_bytes))
    worksheet = workbook.active

    merged_anchor_map = {}
    for merged_range in worksheet.merged_cells.ranges:
        min_col, min_row, max_col, max_row = merged_range.bounds
        anchor = (min_row, min_col)
        for row_num in range(min_row, max_row + 1):
            for col_num in range(min_col, max_col + 1):
                merged_anchor_map[(row_num, col_num)] = anchor

    def write_value(cell_ref: str, value) -> None:
        row_num, col_num = coordinate_to_tuple(cell_ref)
        anchor_row, anchor_col = merged_anchor_map.get((row_num, col_num), (row_num, col_num))
        worksheet.cell(row=anchor_row, column=anchor_col, value=value)

    write_value(REPORT1_TEMPLATE_HEADER_CELL_MAP["year"], year)
    write_value(REPORT1_TEMPLATE_HEADER_CELL_MAP["month"], month)

    for row_idx, (_, row) in enumerate(df.iterrows(), start=REPORT1_TEMPLATE_ROW_START):
        for src_col, col_letter in REPORT1_TEMPLATE_COLUMN_MAP.items():
            if src_col not in df.columns:
                continue
            value = row[src_col]
            write_value(f"{col_letter}{row_idx}", "" if pd.isna(value) else str(value))

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def render_template_preview(template_bytes: bytes, cell_range: str) -> pd.DataFrame:
    workbook = load_workbook(BytesIO(template_bytes), data_only=True)
    worksheet = workbook.active
    min_col, min_row, max_col, max_row = range_boundaries(cell_range)

    data = []
    for row_num in range(min_row, max_row + 1):
        row_data = {"行": row_num}
        for col_num in range(min_col, max_col + 1):
            col_name = get_column_letter(col_num)
            row_data[col_name] = worksheet.cell(row=row_num, column=col_num).value
        data.append(row_data)
    return pd.DataFrame(data)


def apply_placeholder_mappings(worksheet, df: pd.DataFrame, year: int, month: int) -> None:
    def normalize_text(value) -> str:
        text = "" if value is None else str(value)
        return text.replace("\u3000", " ").strip().lower()

    def filter_by_value(source_df: pd.DataFrame, col_name: str, target: str) -> pd.DataFrame:
        normalized_target = normalize_text(target)
        if not normalized_target or normalized_target == "*":
            return source_df

        normalized_series = source_df[col_name].map(normalize_text)
        exact_df = source_df[normalized_series == normalized_target]
        return exact_df

    merged_anchor_map = {}
    for merged_range in worksheet.merged_cells.ranges:
        min_col, min_row, max_col, max_row = merged_range.bounds
        anchor = (min_row, min_col)
        for row_num in range(min_row, max_row + 1):
            for col_num in range(min_col, max_col + 1):
                merged_anchor_map[(row_num, col_num)] = anchor

    def write_value(cell_ref: str, value) -> None:
        row_num, col_num = coordinate_to_tuple(cell_ref)
        anchor_row, anchor_col = merged_anchor_map.get((row_num, col_num), (row_num, col_num))
        worksheet.cell(row=anchor_row, column=anchor_col, value=value)

    # 使用可能な書式:
    # {{年}} / {{月}} / {{固定:文字列}}
    # {{曜日|診療科|時間|診察室}} 例: {{月|内科|午前|101}}
    # 旧形式: {{列名#行番号}} も後方互換で許可
    token_pattern = re.compile(r"^\s*\{\{\s*(.+?)\s*\}\}\s*$")
    for row in worksheet.iter_rows(min_row=1, max_row=worksheet.max_row, min_col=1, max_col=worksheet.max_column):
        for cell in row:
            if not isinstance(cell.value, str):
                continue
            matched = token_pattern.match(cell.value)
            if not matched:
                continue

            token = matched.group(1).strip()
            replacement = ""
            if token == "年":
                replacement = year
            elif token == "月":
                replacement = month
            elif token.startswith("固定:"):
                replacement = token.split(":", 1)[1]
            elif "|" in token or "｜" in token:
                normalized_token = token.replace("｜", "|")
                parts = [part.strip() for part in normalized_token.split("|")]
                if len(parts) >= 3:
                    weekday = parts[0]
                    dept = parts[1]
                    time_slot = parts[2]
                    room = parts[3] if len(parts) >= 4 else ""

                    if weekday in df.columns:
                        candidate_df = df.copy()
                        if "診療科" in candidate_df.columns:
                            candidate_df = filter_by_value(candidate_df, "診療科", dept)
                        if "時間" in candidate_df.columns:
                            candidate_df = filter_by_value(candidate_df, "時間", time_slot)

                        room_col = None
                        for col_name in ["診察室", "部屋番号", "部屋"]:
                            if col_name in candidate_df.columns:
                                room_col = col_name
                                break
                        if room_col:
                            candidate_df = filter_by_value(candidate_df, room_col, room)

                        if len(candidate_df) > 0:
                            src_value = candidate_df.iloc[0][weekday]
                            replacement = "" if pd.isna(src_value) else str(src_value)
            elif "#" in token:
                col_name, row_str = token.split("#", 1)
                col_name = col_name.strip()
                if col_name in df.columns and row_str.isdigit():
                    row_idx = int(row_str) - 1
                    if 0 <= row_idx < len(df):
                        src_value = df.iloc[row_idx][col_name]
                        replacement = "" if pd.isna(src_value) else str(src_value)
            elif token in df.columns and len(df) > 0:
                src_value = df.iloc[0][token]
                replacement = "" if pd.isna(src_value) else str(src_value)

            write_value(cell.coordinate, replacement)

st.set_page_config(layout="wide")
st.title("帳票① 外来担当医表")

conn = get_conn()

col1, col2 = st.columns(2)
with col1:
    year = st.number_input("年", min_value=2020, max_value=2100, value=2026, step=1)
with col2:
    month = st.number_input("月", min_value=1, max_value=12, value=4, step=1)

target_month = f"{int(year)}-{int(month):02d}"

query = load_sql("Report1_pivot.sql")
df = pd.read_sql(query, conn, params={"target_month": target_month})

if df.empty:
    st.warning("対象月のデータがありません")
else:
    display_mode = st.radio(
        "画面表示形式",
        ["改行表示", "区切り表示（ / ）"],
        horizontal=True,
    )

    display_df = df.copy()

    day_cols = ["月", "火", "水", "木", "金", "土"]
    for col in day_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].fillna("")

    if display_mode == "区切り表示（ / ）":
        for col in day_cols:
            if col in display_df.columns:
                display_df[col] = display_df[col].str.replace("\n", " / ")
        st.dataframe(display_df, use_container_width=True)
    else:
        styled_df = display_df.style.set_properties(
            subset=day_cols,
            **{"white-space": "pre-wrap"}
        )
        st.dataframe(styled_df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Excelダウンロード",
        data=csv,
        file_name=f"帳票①_外来担当医表_{target_month}.csv",
        mime="text/csv",
    )

    template_file = st.file_uploader(
        "帳票①Excelテンプレート（.xlsx）",
        type=["xlsx"],
        help=(
            "テンプレートをアップロードすると、見た目（罫線・結合セル）を維持したまま、"
            "担当医表の値を該当セルへ流し込んだExcelを出力します。"
        ),
    )

    if template_file is not None:
        template_bytes = template_file.getvalue()
        st.markdown("#### テンプレート反映設定")
        st.info(
            "推奨: テンプレートにプレースホルダ（例: {{年}}, {{月}}, {{月|内科|午前|101}}）を直接埋め込むと、"
            "大量セルを視覚的に管理できます。"
        )
        st.caption(
            "プレースホルダ書式: {{年}} / {{月}} / {{固定:文字列}} / {{曜日|診療科|時間|診察室}} "
            "（例: {{月|内科|午前|101}}, {{火|外科|午後|*}}, {{固定:休診}}）※ `|` と `｜` の両方可"
        )
        with st.expander("操作ガイド（プレースホルダ方式）", expanded=False):
            st.markdown(
                """
                1. Excelテンプレートの値を入れたいセルに、プレースホルダを直接入力します。  
                2. 例: `{{年}}`, `{{月}}`, `{{月|内科|午前|101}}`, `{{火|外科|午後|*}}`, `{{固定:休診}}`。  
                3. 画面でテンプレートをアップロードし、**テンプレート反映版Excelダウンロード** を押します。  
                4. 出力結果を確認し、必要ならテンプレート側のプレースホルダを修正します。  
                5. `*` はワイルドカードです（例: 部屋番号を問わない場合は `{{月|内科|午前|*}}`）。  
                """
            )
        preview_range = st.text_input("テンプレートプレビュー範囲", value="A1:J20")
        try:
            preview_df = render_template_preview(template_bytes, preview_range)
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"テンプレートプレビューに失敗しました: {exc}")

        try:
            workbook = load_workbook(BytesIO(template_bytes))
            worksheet = workbook.active
            apply_placeholder_mappings(
                worksheet=worksheet,
                df=df,
                year=int(year),
                month=int(month),
            )
            output = BytesIO()
            workbook.save(output)
            filled_excel = output.getvalue()
            st.download_button(
                label="テンプレート反映版Excelダウンロード",
                data=filled_excel,
                file_name=f"帳票①_外来担当医表_{target_month}_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as exc:
            st.error(f"テンプレートExcelへの反映に失敗しました: {exc}")

