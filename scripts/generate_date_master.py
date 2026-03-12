import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# DBファイル
DB_PATH = BASE_DIR / "database" / "schedule.db"

# 作成する期間
start_date = datetime(2025, 4, 1)
end_date = datetime(2031, 3, 31)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

current_date = start_date

while current_date <= end_date:

    calendar_date = current_date.strftime("%Y-%m-%d")
    year_month = current_date.strftime("%Y-%m")

    # 月の第何週か
    week_number = (current_date.day - 1) // 7 + 1

    # 曜日（月=1）
    day_of_week = current_date.weekday() + 1

    cursor.execute("""
        INSERT INTO M_Date
        (CalendarDate, DayOfWeek, WeekNumber, YearMonth)
        VALUES (?, ?, ?, ?)
    """, (calendar_date, day_of_week, week_number, year_month))

    current_date += timedelta(days=1)

conn.commit()
conn.close()

print("M_Date生成完了")