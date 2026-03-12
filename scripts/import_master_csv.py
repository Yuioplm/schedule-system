import sqlite3
import csv
from settings import DB_PATH, CSV_DIR

MASTER_TABLES = [
    ("M_ClinicalDepartment", "M_ClinicalDepartment.csv"),
    ("M_Doctor", "M_Doctor.csv"),
    ("M_ScheduleChangeType", "M_ScheduleChangeType.csv"),
    ("M_Specialty", "M_Specialty.csv")
]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for table, filename in MASTER_TABLES:

    path = CSV_DIR / filename
    print(f"Importing {filename} → {table}")

    with open(path, encoding="utf-8-sig") as f:

        reader = csv.DictReader(f)

        columns = reader.fieldnames
        col_str = ",".join(columns)

        placeholders = ",".join(["?"] * len(columns))

        sql = f"""
        INSERT INTO {table} ({col_str})
        VALUES ({placeholders})
        """

        for row in reader:
            values = [row[col] for col in columns]
            cursor.execute(sql, values)

conn.commit()
conn.close()

print("Master CSV import completed.")