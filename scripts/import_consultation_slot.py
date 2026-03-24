import sqlite3
import csv
from settings import DB_PATH, CSV_DIR

CSV_PATH = CSV_DIR / "T_ConsultationSlot.csv"

def null_if_empty(v):
    return v if v != "" else None


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

success = 0
error = 0

with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:

    reader = csv.DictReader(f)

    for row_no, row in enumerate(reader, start=2):

        try:

            cursor.execute("""
            INSERT INTO T_ConsultationSlot
            (
                Rpt1ClinDeptID,
                Rpt1SpecialtyID,
                Rpt1DisplayDoctorName,
                Rpt2ClinDeptID,
                Rpt3ClinDeptID,
                Rpt4ClinDeptID,
                Rpt5ClinDeptID,
                Rpt6ClinDeptID,
                DoctorID,
                TimeSlotID,
                Room,
                DayOfWeek,
                WeekPattern,
                StartDate,
                EndDate,
                ActiveFlag
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (

                null_if_empty(row["Rpt1ClinDeptID"]),
                null_if_empty(row["Rpt1SpecialtyID"]),
                null_if_empty(row["Rpt1DisplayDoctorName"]),
                null_if_empty(row["Rpt2ClinDeptID"]),
                null_if_empty(row["Rpt3ClinDeptID"]),
                null_if_empty(row["Rpt4ClinDeptID"]),
                null_if_empty(row["Rpt5ClinDeptID"]),
                null_if_empty(row["Rpt6ClinDeptID"]),
                null_if_empty(row["DoctorID"]),
                null_if_empty(row["TimeSlotID"]),
                null_if_empty(row["Room"]),
                row["DayOfWeek"],
                row["WeekPattern"],
                row["StartDate"],
                row["EndDate"],
                row["ActiveFlag"]

            ))

            success += 1

        except Exception as e:

            print("エラー行:", row_no)
            print("内容:", row)
            print("エラー:", e)
            print("-------------------")

            error += 1

conn.commit()
conn.close()

print("取込完了")
print("成功:", success)
print("エラー:", error)