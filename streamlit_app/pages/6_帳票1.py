import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import html
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

def build_report1_html(df: pd.DataFrame, target_month: str) -> str:
    day_cols = ["月", "火", "水", "木", "金", "土"]
    display_df = df.copy()
    columns = list(display_df.columns)
    center_col = "センター" if "センター" in display_df.columns else None
    dept_col = "診療科" if "診療科" in display_df.columns else None
    time_col = "時間" if "時間" in display_df.columns else None

    def same_value(a, b) -> bool:
        return (pd.isna(a) and pd.isna(b)) or (a == b)

    row_count = len(display_df)
    center_span_start = {}
    dept_span_start = {}
    center_run_end = {}
    dept_run_end = {}
    time_span_start = {}

    if center_col is not None and row_count > 0:
        i = 0
        while i < row_count:
            j = i + 1
            while j < row_count and same_value(display_df.iloc[j][center_col], display_df.iloc[i][center_col]):
                j += 1
            center_span_start[i] = j - i
            center_run_end[i] = j
            i = j

    if center_col is not None and dept_col is not None and row_count > 0:
        for center_start, center_end in center_run_end.items():
            k = center_start
            while k < center_end:
                l = k + 1
                while l < center_end and same_value(display_df.iloc[l][dept_col], display_df.iloc[k][dept_col]):
                    l += 1
                dept_span_start[k] = l - k
                dept_run_end[k] = l
                k = l

    if dept_col is not None and time_col is not None and row_count > 0:
        for dept_start, dept_end in dept_run_end.items():
            m = dept_start
            while m < dept_end:
                n = m + 1
                while n < dept_end and same_value(display_df.iloc[n][time_col], display_df.iloc[m][time_col]):
                    n += 1
                time_span_start[m] = n - m
                m = n

    rows_html = []
    for idx, row in display_df.iterrows():
        cells = []
        for col in columns:
            if col == center_col:
                if idx in center_span_start:
                    value = "" if pd.isna(row[col]) else html.escape(str(row[col]))
                    span = center_span_start[idx]
                    cells.append(f'<td class="label-cell center-cell" rowspan="{span}">{value}</td>')
                continue

            if col == dept_col:
                if idx in dept_span_start:
                    value = "" if pd.isna(row[col]) else html.escape(str(row[col]))
                    span = dept_span_start[idx]
                    cells.append(f'<td class="label-cell dept-cell" rowspan="{span}">{value}</td>')
                continue

            if col == time_col:
                if idx in time_span_start:
                    value = "" if pd.isna(row[col]) else html.escape(str(row[col]))
                    span = time_span_start[idx]
                    cells.append(f'<td class="label-cell time-cell" rowspan="{span}">{value}</td>')
                continue

            value = "" if pd.isna(row[col]) else str(row[col])
            escaped = html.escape(value).replace("\n", "<br>")
            cell_class = "day-cell" if col in day_cols else "label-cell"
            if col == "土":
                cell_class += " sat"
            cells.append(f'<td class="{cell_class}">{escaped}</td>')

        rows_html.append("<tr>" + "".join(cells) + "</tr>")

    header_html = "".join([f"<th>{html.escape(str(c))}</th>" for c in columns])
    title_month = target_month.replace("-", "年", 1) + "月"

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>外来担当医表 {html.escape(target_month)}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", sans-serif;
      margin: 20px;
      color: #222;
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: 22px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      font-size: 14px;
      line-height: 1.45;
    }}
    th, td {{
      border: 1px solid #999;
      padding: 8px 6px;
      text-align: center;
      vertical-align: middle;
      word-break: break-word;
    }}
    th {{
      background: #f3f3f3;
      font-weight: 600;
    }}
    .label-cell {{
      background: #fafafa;
    }}
    .center-cell, .dept-cell {{
      background: #f0f7ff;
      font-weight: 600;
    }}
    .time-cell {{
      background: #f7fbf3;
      font-weight: 600;
    }}
    .day-cell {{
      white-space: pre-line;
    }}
    .sat {{
      background: #f5f5f5;
    }}
  </style>
</head>
<body>
  <h1>外来担当医表（{html.escape(title_month)}）</h1>
  <table>
    <thead>
      <tr>{header_html}</tr>
    </thead>
    <tbody>
      {''.join(rows_html)}
    </tbody>
  </table>
</body>
</html>"""


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

        st.markdown("##### データ参照プレビュー（データ行は1始まり）")
        mapping_ref_df = df.copy().reset_index(drop=True)
        mapping_ref_df.insert(0, "データ行", mapping_ref_df.index + 1)
        st.dataframe(mapping_ref_df, use_container_width=True, hide_index=True)

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
            st.caption(
                "現在のマッピング: "
                "年=F1, 月=G1, センター=B列, 診療科=C列, 時間=D列, 月〜土=E〜J列, 開始行=3行目"
            )
        except Exception as exc:
            st.error(f"テンプレートExcelへの反映に失敗しました: {exc}")

    html_content = build_report1_html(df, target_month)
    st.download_button(
        label="HTMLダウンロード",
        data=html_content.encode("utf-8"),
        file_name=f"帳票①_外来担当医表_{target_month}.html",
        mime="text/html",
    )
