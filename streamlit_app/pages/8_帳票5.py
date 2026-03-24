import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
from scripts.settings import get_conn

sys.path.append(str(Path(__file__).resolve().parents[2]))

conn = get_conn()

# ==========================
# 年度選択（プルダウン）
# ==========================
st.title("帳票➄ 常勤・非常勤月別コマ数")

# 年度リスト作成（例：2025〜2027）
years = list(range(2025, 2028))
months = list(range(1, 13))

col1, col2 = st.columns(2)

with col1:
    year = st.selectbox("年度", years, index=1)

with col2:
    month = st.selectbox("月", months, index=datetime.now().month - 1)

# 年度開始日・終了日
start_date = f"{year}-04-01"

if month < 4:
    year = str(int(year) + 1)
date = f"{year}-{month:02d}-01"
end_date = pd.to_datetime(date) + pd.offsets.MonthEnd(1)
end_date = end_date.strftime("%Y-%m-%d")

# ==========================
# SQL（帳票➄ベース）
# ==========================
sql = f"""
-- ==========================
-- 帳票➄
-- ==========================
SELECT
    sa.Rpt1ClinDeptID,
    sa.Rpt5ClinDeptID,

    -- 表示用診療科名
    CASE
        WHEN sa.Rpt5ClinDeptID IS NOT NULL THEN rcd.RptClinDeptName
        ELSE cd.ClinDeptName
    END AS ClinDeptName,
    sa.DoctorID,
    d.DoctorName,
    d.EmploymentType,
    sa.CalendarDate,
    STRFTIME('%Y-%m', sa.CalendarDate) AS Year_month, 

    COUNT(*) AS Cnt

FROM V_ScheduleActual sa

LEFT JOIN M_Doctor d
    ON sa.DoctorID = d.DoctorID

LEFT JOIN M_ReportClinicalDepartment rcd
    ON sa.Rpt5ClinDeptID = rcd.RptClinDeptID

LEFT JOIN M_ClinicalDepartment cd
    ON sa.Rpt1ClinDeptID = cd.ClinDeptID

WHERE
    d.EmploymentType IN ('常勤', '非常勤')
    AND sa.CalendarDate BETWEEN '{start_date}' AND '{end_date}'
    AND (
        (sa.Rpt5ClinDeptID IS NOT NULL AND rcd.ActiveFlag = 1)
        OR
        (sa.Rpt5ClinDeptID IS NULL AND cd.Rpt5Flag = 1)
    )

GROUP BY
    sa.Rpt1ClinDeptID,
    sa.Rpt5ClinDeptID,
    sa.DoctorID,
    ClinDeptName,

    Year_month

ORDER BY
    d.EmploymentType,
    sa.Rpt1ClinDeptID,
    sa.Rpt5ClinDeptID,
    sa.DoctorID,
    sa.CalendarDate
"""

df = pd.read_sql(sql, conn)

# ==========================
# ピボット（横展開）
# ==========================
if not df.empty:

    df["Rpt5ClinDeptID"] = df["Rpt5ClinDeptID"].fillna(0)
    pivot = df.pivot_table(
        index=["EmploymentType", "Rpt1ClinDeptID", "Rpt5ClinDeptID", "ClinDeptName", "DoctorID", "DoctorName"],
        columns="Year_month",
        values="Cnt",
        aggfunc="sum",
        fill_value=0
    )

    # 日付順に並び替え
    pivot = pivot.sort_index(axis=1)

    # 合計列
    pivot["合計"] = pivot.sum(axis=1)

    # ソート（Rpt1優先）
    pivot = pivot.sort_index(level=0)

    pivot = pivot.reset_index()

    # 診療科名にリネーム
    pivot = pivot.rename(columns={
        "ClinDeptName": "診療科名"
    })

    # ID列を削除（ここが今回のゴール）
    pivot = pivot.drop(columns=["Rpt1ClinDeptID", "Rpt5ClinDeptID", "DoctorID"])


    # ==========================
    # 表示
    # ==========================
    st.dataframe(pivot, use_container_width=True)

    # ==========================
    # Excel出力
    # ==========================
    csv = pivot.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="Excelダウンロード",
        data=csv,
        file_name=f"帳票➄_{year}.csv",
        mime="text/csv"
    )

else:
    st.warning("データがありません")