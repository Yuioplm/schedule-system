# Schedule System（外来スケジュール管理）

このリポジトリは、**外来スケジュールの枠管理・予定検索/変更・臨時外来登録・帳票出力・マスタ管理**を行う Streamlit + SQLite アプリです。

---

## 1. 機能概要（現時点）

- **枠管理**: `T_ConsultationSlot` の検索・編集・新規登録（既存枠コピー対応、`Rpt1SpecialtyID`・`Rpt2~Rpt6ClinDeptID` 編集対応）
- **予定検索**: `V_ScheduleFull` を検索し、対象行を変更入力へ受け渡し
- **予定変更入力**: 通常枠の変更登録（`T_ScheduleChange`）
- **臨時外来登録**: タブ画面から `T_TemporarySchedule` を登録
- **帳票①**: 月指定で外来担当医表を表示し、CSV / HTML を出力（必要時に `＜SpecialtyName＞` 付与）
- **帳票②〜⑤**: 期間指定で集計・ピボット出力（CSVダウンロード、帳票③〜⑤は末尾に合計行あり）
- **マスタ管理**: 主要マスタ（診療科・医師・時間帯・専門・帳票診療科・変更種別）を画面編集

---

## 2. データフロー

```text
T_ConsultationSlot + M_Date (+ M_Holiday)
                  └─> V_ScheduleBase
                         + T_ScheduleChange(最新)
                         + T_TemporarySchedule
                  └─> V_ScheduleActual
                             └─> 帳票2/3/4/5

T_ConsultationSlot + M_Date
                  └─> Report1_intermediate.sql
                  └─> Report1_pivot.sql
                             └─> 帳票①（画面/CSV/HTML）
```

---

## 3. 画面一覧

- `pages/1_枠管理.py`
  - フィルタ（診療科/医師/曜日）
  - 既存枠編集（終了日未定=9999-12-31対応）
  - 新規枠登録（マスタ選択 + 既存枠コピー）
  - 帳票関連キー編集（`Rpt1SpecialtyID`, `Rpt2~Rpt6ClinDeptID`）
- `pages/2_予定検索.py`
  - 予定検索と変更対象選択
- `pages/3_予定変更入力.py`
  - タブ1: 通常枠変更登録（`T_ScheduleChange`）
  - タブ2: 臨時外来登録（`T_TemporarySchedule`）
- `pages/4_帳票1.py`
  - 帳票①表示
  - 画面表示モード切替
  - CSV / HTML ダウンロード（セル内に専門名 `＜...＞` 表示対応）
- `pages/5_帳票2.py`〜`pages/8_帳票5.py`
  - 帳票②〜⑤
  - 帳票③〜⑤は合計行を末尾表示
  - 帳票⑤は「選択した年月が属する年度の4月〜選択年月末」で集計
- `pages/9_マスタ管理.py`
  - 主要マスタの検索・編集・新規登録

---

## 4. SQL構成

- `sql/create_tables.sql`
  - テーブル/ビュー定義
  - `M_ClinicalDepartment.Rpt1Sort` を含む
- `sql/Report1_intermediate.sql`
  - 帳票①中間データ生成（ピボット前）
- `sql/Report1_pivot.sql`
  - 帳票①表示用データ（月〜土）
- `sql/Report2.sql`〜`sql/Report5.sql`
  - 帳票②〜⑤（`start_date` / `end_date` パラメータ対応）

> Streamlit 側は `streamlit_app/sql_loader.py` を通して SQL ファイルを読み込みます。

---

## 5. セットアップ

> 前提: Python 3.11 以上推奨

### 5.1 依存関係インストール

```bash
pip install -r requirements.txt
```

### 5.2 初期セットアップ

```bash
python set_up.py
```

このコマンドで以下を順次実行します。

- `scripts/init_db.py`
- `scripts/import_master_csv.py`
- `scripts/generate_date_master.py`
- `scripts/generate_holiday_master.py`
- `scripts/import_consultation_slot.py`
- `scripts/fix_date_format.py`

### 5.3 起動

```bash
streamlit run streamlit_app/app.py
```

初回起動で `Welcome to Streamlit!` のメール入力プロンプトが止まる問題を避けるため、
このリポジトリでは `.streamlit/config.toml` で `gatherUsageStats = false` を設定し、
`.streamlit/credentials.toml` で `email = ""` を明示しています。
起動後はターミナルに表示される `Local URL`（通常 `http://localhost:8501`）へアクセスしてください。

それでも同メッセージが表示される場合は、以下のようにオプションを明示して起動してください。

```bash
streamlit run streamlit_app/app.py --browser.gatherUsageStats false --server.headless true
```

---

## 6. よく使う運用ポイント

- **終了日未定**は DB では `9999-12-31` を使用
  - UI上は Streamlit制約により安全な日付に丸めて表示
  - チェックボックスで「終了日未定」を制御
- **帳票条件の主軸**
  - 帳票①: `Rpt1ClinDeptID`, `Rpt1Flag`, `Rpt1Sort`
  - 帳票②〜⑤: 各 `RptXClinDeptID`, `RptXFlag`
- **帳票⑤の期間仕様**
  - 年月選択に対して、開始は該当年度の4/1、終了は選択年月の月末
- **SQL変更時の原則**
  - SQLは `sql/` に集約
  - ページ側は `load_sql()` + `params` で実行

---

## 7. ディレクトリ（抜粋）

```text
Schedule-System/
├─ README.md
├─ set_up.py
├─ requirements.txt
├─ sql/
│  ├─ create_tables.sql
│  ├─ Report1_intermediate.sql
│  ├─ Report1_pivot.sql
│  ├─ Report2.sql
│  ├─ Report3.sql
│  ├─ Report4.sql
│  └─ Report5.sql
├─ scripts/
│  ├─ settings.py
│  ├─ init_db.py
│  ├─ import_master_csv.py
│  ├─ generate_date_master.py
│  ├─ generate_holiday_master.py
│  └─ import_consultation_slot.py
└─ streamlit_app/
   ├─ app.py
   ├─ sql_loader.py
   └─ pages/
      ├─ 1_枠管理.py
      ├─ 2_予定検索.py
      ├─ 3_予定変更入力.py
      ├─ 4_帳票1.py
      ├─ 5_帳票2.py
      ├─ 6_帳票3.py
      ├─ 7_帳票4.py
      ├─ 8_帳票5.py
      └─ 9_マスタ管理.py
```

---

## 8. 補足

- DBファイル: `database/schedule.db`
- 取込CSV: `csv/` 配下（`M_*.csv`, `T_ConsultationSlot.csv`）
