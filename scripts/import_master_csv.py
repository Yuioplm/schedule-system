import sqlite3
import csv
from pathlib import Path
from settings import DB_PATH, CSV_DIR

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=== Import Master CSV ===")

# M_で始まるCSVを自動取得
csv_files = sorted(CSV_DIR.glob("M_*.csv"))

for csv_path in csv_files:

    table_name = csv_path.stem

    print(f"Importing {csv_path.name} → {table_name}")

    with open(csv_path, encoding="utf-8-sig") as f:

        reader = csv.DictReader(f)

        columns = reader.fieldnames

        col_str = ",".join(columns)

        placeholders = ",".join(["?"] * len(columns))

        sql = f"""
        INSERT INTO {table_name} ({col_str})
        VALUES ({placeholders})
        """

        for row in reader:

            values = [row[col] for col in columns]

            cursor.execute(sql, values)

conn.commit()
conn.close()

print("Master CSV import completed.")
