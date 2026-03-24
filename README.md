# Schedule System（外来スケジュール管理）

このリポジトリは、**外来スケジュールのテンプレート管理・検索・予定変更登録・帳票出力**を行う Streamlit + SQLite のアプリケーションです。

---

## 1. まず理解する全体像

本システムは、以下の流れで動作します。

1. テンプレート枠（`T_ConsultationSlot`）を管理する。
2. 日付マスタ（`M_Date`）と突合して「当日の通常枠」を展開する（`V_ScheduleBase`）。
3. 変更履歴（`T_ScheduleChange`）の最新有効レコードを重ねる。
4. 臨時外来（`T_TemporarySchedule`）を追加する。
5. 最終的な実績ビュー（`V_ScheduleActual`）を帳票や集計に使う。

```text
T_ConsultationSlot + M_Date + M_Holiday
                  └─> V_ScheduleBase
                         + T_ScheduleChange(最新)
                         + T_TemporarySchedule
                  └─> V_ScheduleActual
                             └─> 帳票2/3/4/5
```

---

## 2. ディレクトリ構成

```text
Schedule-System/
├─ set_up.py                      # 初期セットアップ一括実行
├─ requirements.txt               # Python依存関係
├─ scripts/                       # DB初期化・データ投入スクリプト
│  ├─ settings.py                 # DB/CSV/SQLパス定義
│  ├─ init_db.py                  # create_tables.sql 実行
│  ├─ import_master_csv.py        # M_*.csv 自動投入
│  ├─ generate_date_master.py     # M_Date 生成
│  ├─ generate_holiday_master.py  # M_Holiday 生成
│  ├─ import_consultation_slot.py # T_ConsultationSlot.csv 投入
│  └─ fix_date_format.py          # 日付フォーマット正規化
├─ sql/
│  ├─ create_tables.sql           # テーブル・ビュー定義
│  ├─ Report2.sql ~ Report5.sql   # 帳票SQL（参照用）
└─ streamlit_app/
   ├─ app.py                      # メニュー
   └─ pages/
      ├─ 1_枠管理.py
      ├─ 2_予定検索.py
      ├─ 3_予定変更入力.py
      ├─ 5_帳票2.py
      ├─ 6_帳票3.py
      ├─ 7_帳票4.py
      └─ 8_帳票5.py
```

---

## 3. クイックスタート（最短セットアップ）

> 前提: Python 3.11 以上推奨

### 3.1 依存関係をインストール

```bash
pip install -r requirements.txt
```

### 3.2 初期データセットアップ

```bash
python set_up.py
```

このコマンドで、次の順に実行されます。

- `scripts/init_db.py`
- `scripts/import_master_csv.py`
- `scripts/generate_date_master.py`
- `scripts/generate_holiday_master.py`
- `scripts/import_consultation_slot.py`
- `scripts/fix_date_format.py`

### 3.3 アプリ起動

```bash
streamlit run streamlit_app/app.py
```

---

## 4. 画面別データフロー（まずここを読む）

### 4.1 枠管理（`pages/1_枠管理.py`）

- `T_ConsultationSlot` の先頭100件表示。
- フォームから新規枠を追加（INSERT）。

```text
画面入力 -> T_ConsultationSlot
```

### 4.2 予定検索（`pages/2_予定検索.py`）

- `V_ScheduleFull` から期間・診療科・医師で検索。
- 行ごとの「変更」ボタンで `st.session_state.selected` に対象行を入れて、変更入力画面へ遷移。

```text
V_ScheduleFull -> 検索表示 -> 選択行を session_state に保存 -> 予定変更入力へ
```

### 4.3 予定変更入力（`pages/3_予定変更入力.py`）

- 予定検索で選択された行を表示。
- 変更種別、代診医、詳細、備考などを入力。
- `T_ScheduleChange` にINSERT。

```text
session_state.selected + マスタ参照 -> 入力 -> T_ScheduleChange
```

### 4.4 帳票2〜5（`pages/5_帳票2.py`〜`8_帳票5.py`）

- `V_ScheduleBase` / `V_ScheduleActual` を中心に SQL で抽出。
- pandas でピボット・整形し、CSVダウンロード提供。

```text
ビュー/テーブル -> SQL抽出 -> pandas整形 -> 表示 + CSV
```

---

## 5. 新規参加者が最初に押さえる重要ポイント

1. **実績系の起点は `V_ScheduleActual`**
   - 通常枠 + 最新変更 + 臨時外来を統合。
2. **帳票は `RptXClinDeptID` と `RptXFlag` で対象制御**
   - 「どの帳票に出るか」は診療科IDとフラグに依存。
3. **日付生成範囲は固定（2025-04-01〜2031-03-31）**
   - 年度更新時に見直し必須。
4. **予定変更入力は現状、時間帯/部屋変更が無効化された実装**
   - 変更要件が入る場合はこの画面の仕様確認が先。
5. **曜日・週パターン整合性は要注意**
   - `M_Date.DayOfWeek` と入力値の扱い差分を確認すること。

---

## 6. 典型的な改修ガイド

### 6.1 画面表示を変えたい

- 対応ページ（`streamlit_app/pages/*.py`）を編集。
- SQL変更が必要なら、対象ビューとJOIN先を同時に確認。

### 6.2 帳票条件を変えたい

- まず `pages/5~8_帳票*.py` のWHERE句を確認。
- 必要に応じて `sql/create_tables.sql` のビュー定義やフラグ設計を更新。

### 6.3 新しいマスタを追加したい

1. `sql/create_tables.sql` にテーブル追加。
2. CSV投入設計（`M_*.csv`）に合わせる。
3. 画面/帳票のJOINに反映。

---

## 7. 学習ロードマップ（推奨順）

1. `sql/create_tables.sql` を読み、テーブルとビュー連鎖を理解。
2. `set_up.py` と `scripts/` の実行順を追う。
3. `pages/2_予定検索.py` → `pages/3_予定変更入力.py` の画面遷移を追う。
4. 帳票ページ（2〜5）のSQLとpandas整形を比較し、共通化余地を把握。

---

## 8. よく使うコマンド

```bash
# セットアップ
python set_up.py

# アプリ起動
streamlit run streamlit_app/app.py

# 変更確認
git status
```

---

## 9. 補足

- 実データ投入用の `csv/` ディレクトリ（`M_*.csv`, `T_ConsultationSlot.csv`）が必要です。
- DBファイルは `database/schedule.db` を使用します。

