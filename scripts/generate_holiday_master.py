import sqlite3
from datetime import date, timedelta
import jpholiday
from settings import DB_PATH

start_date = date(2025, 4, 1)
end_date = date(2031, 3, 31)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

current = start_date

while current <= end_date:

    # 日本の祝日
    if jpholiday.is_holiday(current):
        name = jpholiday.is_holiday_name(current)

        cursor.execute("""
        INSERT INTO M_Holiday (HolidayDate, HolidayName)
        VALUES (?, ?)
        """, (current.isoformat(), name))

    # 年末年始
    if (current.month == 12 and current.day in [30, 31]) or \
       (current.month == 1 and current.day in [2, 3]):

        cursor.execute("""
        INSERT INTO M_Holiday (HolidayDate, HolidayName)
        VALUES (?, ?)
        """, (current.isoformat(), "年末年始"))

    current += timedelta(days=1)

conn.commit()
conn.close()

print("祝日生成完了")