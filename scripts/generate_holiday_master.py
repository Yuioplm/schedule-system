import sqlite3
from datetime import date, timedelta
import jpholiday
from settings import DB_PATH, fiscal_year_date_range

start_date_str, end_date_str = fiscal_year_date_range()
start_date = date.fromisoformat(start_date_str)
end_date = date.fromisoformat(end_date_str)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

current = start_date

while current <= end_date:

    # 日本の祝日
    if jpholiday.is_holiday(current):
        name = jpholiday.is_holiday_name(current)

        cursor.execute("""
        INSERT INTO M_Holiday (HolidayDate, HolidayName)
        SELECT ?, ?
        WHERE NOT EXISTS (
            SELECT 1
            FROM M_Holiday
            WHERE HolidayDate = ?
              AND HolidayName = ?
        )
        """, (current.isoformat(), name, current.isoformat(), name))

    # 年末年始
    if (current.month == 12 and current.day in [30, 31]) or \
       (current.month == 1 and current.day in [2, 3]):

        cursor.execute("""
        INSERT INTO M_Holiday (HolidayDate, HolidayName)
        SELECT ?, ?
        WHERE NOT EXISTS (
            SELECT 1
            FROM M_Holiday
            WHERE HolidayDate = ?
              AND HolidayName = ?
        )
        """, (current.isoformat(), "年末年始", current.isoformat(), "年末年始"))

    current += timedelta(days=1)

conn.commit()
conn.close()

print("祝日生成完了")
