import sqlite3
from datetime import datetime
from settings import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")


# -------------------------
# 祝日取得
# -------------------------

cursor.execute("""
SELECT HolidayDate
FROM M_Holiday
""")

holiday_set = {row[0] for row in cursor.fetchall()}


# -------------------------
# 日付マスタ取得
# -------------------------

cursor.execute("""
SELECT CalendarDate, DayOfWeek, WeekNumber
FROM M_Date
""")

dates = cursor.fetchall()


# -------------------------
# Slot取得
# -------------------------

cursor.execute("""
SELECT
    SlotID,
    ClinDeptID,
    DoctorID,
    TimeSlotID,
    Room,
    DayOfWeek,
    WeekPattern,
    StartDate,
    EndDate,
    ActiveFlag
FROM T_ConsultationSlot
WHERE ActiveFlag = 1
""")

slots = cursor.fetchall()


insert_count = 0


# -------------------------
# 予定生成
# -------------------------

for slot in slots:

    (
        slot_id,
        clin_dept,
        doctor,
        time_slot,
        room,
        slot_dow,
        week_pattern,
        start_date,
        end_date,
        active
    ) = slot


    for date in dates:

        cal_date, dow, week_no = date


        # 曜日チェック
        if dow != slot_dow:
            continue


        # 有効期間
        if cal_date < start_date or cal_date > end_date:
            continue


        # 祝日除外
        if cal_date in holiday_set:
            continue


        # WeekPattern判定
        # week_no は 1〜5
        if week_no > len(week_pattern):
            continue

        if week_pattern[week_no - 1] != "1":
            continue


        try:

            cursor.execute("""
            INSERT OR IGNORE INTO T_Schedule
            (
                CalendarDate,
                SlotID,
                DoctorID,
                ClinDeptID,
                TimeSlotID,
                Room
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, (

                cal_date,
                slot_id,
                doctor,
                clin_dept,
                time_slot,
                room

            ))

            insert_count += 1

        except Exception as e:

            print("エラー:", e)
            print("SlotID:", slot_id)
            print("Date:", cal_date)


conn.commit()
conn.close()

print("予定生成完了")
print("生成件数:", insert_count)