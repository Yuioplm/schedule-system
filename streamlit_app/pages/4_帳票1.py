import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import html

from scripts.settings import get_conn

sys.path.append(str(Path(__file__).resolve().parents[2]))

from streamlit_app.sql_loader import load_sql


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

    html_content = build_report1_html(df, target_month)
    st.download_button(
        label="HTMLダウンロード",
        data=html_content.encode("utf-8"),
        file_name=f"帳票①_外来担当医表_{target_month}.html",
        mime="text/html",
    )
