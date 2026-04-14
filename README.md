# Schedule System（外来スケジュール管理）

このリポジトリは、**外来スケジュールの枠管理・予定変更・反映後予定検索・変更履歴管理・帳票出力・マスタ管理**を行う、
**Streamlit + SQLite** ベースのアプリケーションです。

現時点の実装に合わせ、READMEを更新しています。

---

## 1. システム概要（現行実装ベース）

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
   - 枠検索・編集・新規登録
   - `9999-12-31`（終了日未定）をUI上で安全日付へ補正して扱う
2. **予定検索**（`2_予定検索.py`）
   - `V_ScheduleFull` 検索
   - 選択行をセッション経由で変更入力画面へ連携
3. **予定変更入力**（`3_予定変更入力.py`）
   - タブ1: 通常枠変更（`T_ScheduleChange`）
   - タブ2: 臨時外来登録（`T_TemporarySchedule`）
4. **反映後予定検索**（`4_反映後予定検索.py`）
   - `V_ScheduleActual` 検索
5. **変更登録履歴検索**（`5_変更登録履歴.py`）
   - 変更履歴検索
   - Excelテンプレートへのプレースホルダ反映出力（画像保持考慮）
6. **帳票① 外来担当医表**（`6_帳票1.py`）
   - 院内用/外部用切替（`Report1_pivot.sql` / `Report1_pivot_external.sql`）
   - 画面表示、CSV出力、Excelテンプレート反映出力
7. **帳票② 予定変更一覧**（`7_帳票2.py`）
8. **帳票③ 外来数**（`8_帳票3.py`）
   - 日別ピボット + 合計行
9. **帳票④ 常勤日別コマ数**（`9_帳票4.py`）
   - 日別ピボット + 合計行
10. **帳票⑤ 常勤・非常勤月別コマ数**（`10_帳票5.py`）
    - 年度開始（4月）〜選択月末で集計 + 合計行
11. **帳票⑥ 非常勤医師勤務報告書**（`11_帳票6.py`）
    - 対象月の非常勤医師抽出（予定/実績ベース）
    - 日別 AM/PM 勤務・備考プレビュー
    - 医師別シートをExcelテンプレートから一括生成
12. **マスタ管理**（`12_マスタ管理.py`）
    - 診療科・医師・時間帯・専門・帳票診療科・変更種別を画面編集

---

## 4. SQLファイル構成（`sql/`）

- `create_tables.sql`
  - 全テーブル・ビュー定義（`V_ScheduleBase` / `V_ScheduleFull` / `V_ScheduleActual` 含む）
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

`set_up.py` では以下を順に実行します。

1. `scripts/init_db.py`
2. `scripts/import_master_csv.py`
3. `scripts/generate_date_master.py`
4. `scripts/generate_holiday_master.py`
5. `scripts/import_consultation_slot.py`
6. `scripts/fix_date_format.py`

補助スクリプト:

- `scripts/fix_weekpattern_db.py`
  - `T_ConsultationSlot.WeekPattern` のゼロ埋め補正
- `scripts/reports.py`
  - 帳票ロジック検証用のPython実装（現行UIの主経路はSQL + Streamlitページ）

### 5.3 起動

```bash
streamlit run streamlit_app/app.py
```

---

## 6. 運用ルール（現行実装で重要な点）

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
├─ logs/  （実行時生成・Git管理外）
├─ requirements.txt
├─ set_up.py
├─ scripts/
│  ├─ settings.py
│  ├─ init_db.py
│  ├─ import_master_csv.py
│  ├─ import_consultation_slot.py
│  ├─ generate_date_master.py
│  ├─ generate_holiday_master.py
│  ├─ fix_date_format.py
│  ├─ fix_weekpattern_db.py
│  └─ reports.py
├─ sql/
│  ├─ create_tables.sql
│  ├─ Report1_intermediate.sql
│  ├─ Report1_pivot.sql
│  ├─ Report1_pivot_external.sql
│  ├─ Report2.sql
│  ├─ Report3.sql
│  ├─ Report4.sql
│  ├─ Report5.sql
│  ├─ Report6_daily_status.sql
│  ├─ Report6_doctors.sql
│  └─ Report6_eligible_doctors.sql
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
- アプリログ: `logs/app.log`（ローテーション: 10MB × 10世代）

---

## 9. Windows向け運用バッチ（朝の起動 / 夜のバックアップ）

`ops/windows/` 配下に、ワンクリック実行用の `.bat` を用意しています。

- `start_app.bat`
  - 仮想環境 (`.venv`) があれば自動有効化
  - `streamlit run streamlit_app/app.py --server.address 0.0.0.0 --server.port 8501` で起動
- `start_app_silent.vbs`
  - `start_app.bat` を**コマンドプロンプト非表示**で起動
  - 運用担当者向けの通常起動はこちらを推奨
- `backup_db.bat`
  - `database/schedule.db` を `backups` フォルダへ日時付きでコピー
  - 直近30日より古いバックアップを自動削除
- `stop_app.bat`
  - `8501` ポートで待受中のプロセスを停止（`taskkill`）

### 9.1 使い方

1. 朝: `ops/windows/start_app_silent.vbs` をダブルクリック（非表示起動）
   - トラブル調査時のみ `start_app.bat` を直接実行（エラーメッセージ確認用）
2. 夜: `ops/windows/backup_db.bat` をダブルクリック

`start_app.bat` は Streamlit をバックグラウンド起動（コンソール非表示）します。
起動後は `http://localhost:8501` にアクセスしてください。

### 9.2 終了方法（シャットダウン以外）

`start_app.bat` はバックグラウンド起動のため、
終了時は `ops/windows/stop_app.bat` を実行してください（ポート 8501 の待受プロセスを停止）。

### 9.3 起動しない場合の確認

`start_app.bat` は起動時に以下を自動チェックします。

- `streamlit_app/app.py` の存在
- Python 実行環境（`venv` 優先、次に `.venv`。どちらも無ければ `venv` を自動作成）
- `streamlit` パッケージの存在（未インストール時は `requirements.txt` から自動導入）

`venv` の自動作成や依存自動導入に失敗した場合は、
表示内容に従って対応してください（例: ネットワーク/プロキシ設定確認）。

※ `activate` 実行は必須ではありません。`venv\Scripts\python.exe` を直接呼び出して起動します。

運用時の実行ログは `logs/app.log` に出力されます（Git管理対象外）。

### 9.4 接続先URL

運用PCで `hostname` を実行し、表示されたPC名を使います。

例:

```text
http://<PC名>:8501
```

---

## 10. 担当者用マニュアル

日次運用（起動・登録・帳票出力・バックアップ終了）の手順を、担当者向けに別紙化しています。

- `docs/担当者マニュアル.md`

特に、業務終了時はアプリのサイドバーにある **「💾 バックアップして終了」** の利用を推奨します。
