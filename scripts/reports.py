import pandas as pd
from scripts.settings import get_conn


def report3(month):
    """
    帳票③
    常勤医師の日別担当枠数

    month : 'YYYY-MM'
    """

    conn = get_conn()

    sql = """
    SELECT
        sa.CalendarDate,
        cd.ClinDeptID,
        cd.ClinDeptName,
        d.DoctorID,
        d.DoctorName

    FROM V_ScheduleActual sa

    JOIN M_Doctor d
        ON sa.DoctorID = d.DoctorID

    JOIN M_ClinicalDepartment cd
        ON sa.ClinDeptID = cd.ClinDeptID

    WHERE
        strftime('%Y-%m', sa.CalendarDate) = ?
        AND d.EmploymentType = '常勤'
        AND cd.ReportTargetFlag = 1
    """

    df = pd.read_sql(sql, conn, params=(month,))

    if df.empty:
        return pd.DataFrame()

    # 日付 → 日
    df["Day"] = pd.to_datetime(df["CalendarDate"]).dt.day

    # pivot
    pivot = df.pivot_table(
        index=[
            "ClinDeptID",
            "ClinDeptName",
            "DoctorID",
            "DoctorName"
        ],
        columns="Day",
        aggfunc="size",
        fill_value=0
    )

    # 合計
    pivot["合計"] = pivot.sum(axis=1)

    # 並び替え
    pivot = pivot.sort_index(level=[0, 2])

    # index解除
    pivot = pivot.reset_index()

    # ID列は帳票では不要なので削除
    pivot = pivot.drop(columns=["ClinDeptID", "DoctorID"])

    return pivot