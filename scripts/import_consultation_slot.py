import sqlite3
import csv
import sys
import unicodedata
from settings import DB_PATH, CSV_DIR

CSV_PATH = CSV_DIR / "T_ConsultationSlot.csv"

def normalize(v):
    if v is None:
        return None
    normalized = unicodedata.normalize("NFKC", v).strip()
    return normalized if normalized != "" else None


def to_int_or_none(v):
    normalized = normalize(v)
    return int(normalized) if normalized is not None else None


def safe_print_row(row):
    line = str(row)
    encoding = sys.stdout.encoding or "utf-8"
    print(line.encode(encoding, errors="backslashreplace").decode(encoding))


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

                to_int_or_none(row["Rpt1ClinDeptID"]),
                to_int_or_none(row["Rpt1SpecialtyID"]),
                normalize(row["Rpt1DisplayDoctorName"]),
                to_int_or_none(row["Rpt2ClinDeptID"]),
                to_int_or_none(row["Rpt3ClinDeptID"]),
                to_int_or_none(row["Rpt4ClinDeptID"]),
                to_int_or_none(row["Rpt5ClinDeptID"]),
                to_int_or_none(row["Rpt6ClinDeptID"]),
                to_int_or_none(row["DoctorID"]),
                to_int_or_none(row["TimeSlotID"]),
                normalize(row["Room"]),
                int(normalize(row["DayOfWeek"])),
                normalize(row["WeekPattern"]),
                normalize(row["StartDate"]),
                normalize(row["EndDate"]),
                int(normalize(row["ActiveFlag"]))

            ))

            success += 1

        except Exception as e:

            print("エラー行:", row_no)
            print("内容:", end=" ")
            safe_print_row(row)
            print("エラー:", e)
            print("-------------------")

            error += 1

conn.commit()
conn.close()

print("取込完了")
print("成功:", success)
print("エラー:", error)
