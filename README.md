# Schedule System（外来スケジュール管理）

このリポジトリは、**外来スケジュールの枠管理・予定変更・反映後予定検索・変更履歴管理・帳票出力・マスタ管理**を行う、
**Streamlit + SQLite** ベースのアプリケーションです。

---

## 1. システム概要

- **基盤データ**は `T_ConsultationSlot`（診療枠テンプレート）と `M_Date`（日付マスタ）を起点に生成
- **予定変更**は `T_ScheduleChange`（通常枠の変更履歴）に登録
- **臨時外来**は `T_TemporarySchedule` に登録
- **反映後予定**はビュー `V_ScheduleActual` で統合（通常枠 + 最新変更 + 臨時外来）
- 各帳票ページは `sql/*.sql` を `streamlit_app/sql_loader.py` で読み込み実行
- アプリログは `streamlit_app/logging_config.py` で設定し、`logs/app.log` にローテーション保存（10MB × 10世代）

---

## 2. 主要データモデル

### 2.1 マスタ

- `M_ClinicalDepartment`（診療科、帳票フラグ `Rpt1Flag`〜`Rpt6Flag` 等）
- `M_Specialty`（専門）
- `M_ReportClinicalDepartment`（帳票用診療科）
- `M_Doctor`（医師、所属、勤務形態）
- `M_TimeSlot`（時間帯）
- `M_Date`（日付、曜日、週番号、年月）
- `M_Holiday`（祝日・年末年始）
- `M_ScheduleChangeType`（変更種別）

### 2.2 トランザクション

- `T_ConsultationSlot`（通常枠テンプレート）
  - `Rpt1ClinDeptID` / `Rpt1SpecialtyID` / `Rpt1DisplayDoctorName`
  - `Rpt2ClinDeptID`〜`Rpt6ClinDeptID`
  - `WeekPattern`（第1〜第5週の適用）
  - `StartDate`〜`EndDate`（有効期間）
- `T_ScheduleChange`（通常枠の変更登録）
  - 変更後医師・時間帯・部屋、変更内容、備考、`Rpt2Flag` など
  - 同一日付・同一枠では **最新 `ChangeID`** を有効変更として扱う
- `T_TemporarySchedule`（臨時外来登録）
  - Rpt系カラムを保持し、`V_ScheduleActual` に統合

### 2.3 ビュー

- `V_ScheduleBase`
  - `M_Date` × `T_ConsultationSlot`
  - 有効期間・`WeekPattern`・有効フラグで絞り込み
  - `M_Holiday` を用いて祝日除外
- `V_ScheduleFull`
  - `V_ScheduleBase` に診療科/専門/医師/時間帯名を付加（予定検索向け）
- `V_ScheduleActual`
  - 通常枠 + 最新変更（取消除外） + 臨時外来 を統合（反映後予定・帳票向け）

---

## 3. 画面構成（`streamlit_app/pages`）

1. **枠管理**（`1_枠管理.py`）
2. **予定検索**（`2_予定検索.py`）
3. **予定変更入力**（`3_予定変更入力.py`）
4. **反映後予定検索**（`4_反映後予定検索.py`）
5. **変更登録履歴検索**（`5_変更登録履歴.py`）
6. **帳票① 外来担当医表**（`6_帳票1.py`）
7. **帳票② 予定変更一覧**（`7_帳票2.py`）
8. **帳票③ 外来数**（`8_帳票3.py`）
9. **帳票④ 常勤日別コマ数**（`9_帳票4.py`）
10. **帳票⑤ 常勤・非常勤月別コマ数**（`10_帳票5.py`）
11. **帳票⑥ 非常勤医師勤務報告書**（`11_帳票6.py`）
12. **マスタ管理**（`12_マスタ管理.py`）

---

## 4. SQLファイル構成（`sql/`）

- `create_tables.sql`（全テーブル・ビュー定義）
- 帳票系SQL
  - `Report1_intermediate.sql`
  - `Report1_pivot.sql`
  - `Report1_pivot_external.sql`
  - `Report2.sql`
  - `Report3.sql`
  - `Report4.sql`
  - `Report5.sql`
  - `Report6_daily_status.sql`
  - `Report6_doctors.sql`
  - `Report6_eligible_doctors.sql`

---

## 5. 初期セットアップ

> 前提: Python 3.11 以上推奨

### 5.1 依存インストール

```bash
pip install -r requirements.txt
```

### 5.2 DB・初期データ作成

```bash
python set_up.py
```

`set_up.py` 実行内容:

1. `scripts/init_db.py`
2. `scripts/import_master_csv.py`
3. `scripts/generate_date_master.py`
4. `scripts/generate_holiday_master.py`
5. `scripts/import_consultation_slot.py`
6. `scripts/fix_date_format.py`

### 5.3 起動

```bash
streamlit run streamlit_app/app.py
```

---

## 6. 運用ルール（重要）

- **終了日未定**はDBで `9999-12-31` を使用
- **帳票キー**は `T_ConsultationSlot` / `T_TemporarySchedule` の `Rpt1〜Rpt6` 系カラムで管理
- **予定変更の反映**は「同一日・同一枠の最新変更」を採用
- **帳票②表示制御**には `Rpt2Flag` を使用
- **祝日除外**は `V_ScheduleBase` 生成時点で適用

---

## 7. ディレクトリ構成

```text
Schedule-System/
├─ README.md
├─ docs/
│  └─ 担当者マニュアル.md
├─ logs/  （実行時生成・Git管理外）
├─ requirements.txt
├─ set_up.py
├─ scripts/
├─ sql/
├─ ops/
│  └─ windows/
│     ├─ start_app.bat
│     ├─ start_app_silent.vbs
│     ├─ backup_db.bat
│     └─ stop_app.bat
└─ streamlit_app/
   ├─ app.py
   ├─ sql_loader.py
   └─ pages/
      ├─ 1_枠管理.py
      ├─ 2_予定検索.py
      ├─ 3_予定変更入力.py
      ├─ 4_反映後予定検索.py
      ├─ 5_変更登録履歴.py
      ├─ 6_帳票1.py
      ├─ 7_帳票2.py
      ├─ 8_帳票3.py
      ├─ 9_帳票4.py
      ├─ 10_帳票5.py
      ├─ 11_帳票6.py
      └─ 12_マスタ管理.py
```

---

## 8. パス設定

- DBファイル: `database/schedule.db`
- マスタCSV: `csv/M_*.csv`
- 初期枠CSV: `csv/T_ConsultationSlot.csv`
- アプリログ: `logs/app.log`
- ランタイム一時領域（Windowsバッチ起動時）: `.runtime/`

---

## 9. Windows向け運用バッチ

`ops/windows/` 配下のバッチで、起動・停止・バックアップを実施できます。

### 9.1 起動

- 推奨: `start_app_silent.vbs`（`start_app.bat` を非表示起動）
- `start_app.bat` の主な動作
  - `venv` → `.venv` の順で仮想環境を探索
  - 見つからない場合は `venv` を自動作成
  - `streamlit` 未導入時は `requirements.txt` から自動導入
  - `streamlit_app/app.py` を **バックグラウンド起動**
  - ブラウザ（Edge/Chrome）を専用ウィンドウで開く（見つからない場合は既定ブラウザ）

### 9.2 バックアップ

- `backup_db.bat`
  - `database/schedule.db` を `backups/schedule_yyyyMMdd_HHmmss.db` へコピー
  - `30日より古い` バックアップを自動削除

### 9.3 停止

- `stop_app.bat`
  - ポート `8501` の待受プロセスを停止
  - 起動時に開いた専用ブラウザウィンドウも終了対象

### 9.4 URL

- 同一PCで利用: `http://localhost:8501`
- 他端末から接続: `http://<運用PC名>:8501`

---

## 10. 担当者用マニュアル

日次運用（起動・登録・帳票出力・バックアップ終了）手順は、以下を参照してください。

- `docs/担当者マニュアル.md`

Windows環境では、サイドバーの **「💾 バックアップして終了」** から、
バックアップと停止処理を一括実行できます（`backup_db.bat` → `stop_app.bat`）。
