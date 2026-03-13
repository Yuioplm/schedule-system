import sqlite3
from settings import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# WeekPatternを取得
cursor.execute("""
SELECT SlotID, WeekPattern
FROM T_ConsultationSlot
""")

rows = cursor.fetchall()

for slot_id, week_pattern in rows:

    if week_pattern is None:
        continue

    # 文字列化して5桁ゼロ埋め
    fixed = str(week_pattern).zfill(5)

    # 更新
    cursor.execute("""
    UPDATE T_ConsultationSlot
    SET WeekPattern = ?
    WHERE SlotID = ?
    """, (fixed, slot_id))

conn.commit()
conn.close()

print("WeekPattern 修正完了")