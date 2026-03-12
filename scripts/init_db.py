import sqlite3
from settings import DB_PATH, BASE_DIR

# SQLファイル
SQL_DIR = BASE_DIR / "sql"
CREATE_TABLE_SQL = SQL_DIR / "create_tables.sql"

# SQLファイルを読み込む
with open(CREATE_TABLE_SQL, "r", encoding="utf-8") as f:
    sql = f.read()

# SQLiteに接続
conn = sqlite3.connect(DB_PATH)

# SQLをまとめて実行
conn.executescript(sql)

# 保存
conn.commit()

# 接続終了
conn.close()

print("データベース作成完了")