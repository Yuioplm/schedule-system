import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# DBファイル
DB_PATH = BASE_DIR / "database" / "schedule.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


def normalize_date(date_str):
    if date_str is None:
        return None

    # 2025/4/1 → datetime
    d = datetime.strptime(date_str, "%Y/%m/%d")

    # 2025-04-01
    return d.strftime("%Y-%m-%d")


# -----------------------------
# ConsultationSlot修正
# -----------------------------

cursor.execute("""
SELECT SlotID, StartDate, EndDate
FROM T_ConsultationSlot
""")

rows = cursor.fetchall()

for slot_id, start_date, end_date in rows:

    new_start = normalize_date(start_date)
    new_end = normalize_date(end_date)

    cursor.execute("""
    UPDATE T_ConsultationSlot
    SET StartDate=?, EndDate=?
    WHERE SlotID=?
    """, (new_start, new_end, slot_id))


conn.commit()
conn.close()

print("日付フォーマット修正完了")