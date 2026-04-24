# Schedule System（外来スケジュール管理）

このリポジトリは、**外来スケジュールの枠管理・予定変更・反映後予定検索・変更履歴編集・帳票出力・マスタ管理**を行う、
**Streamlit + SQLite** ベースのアプリケーションです。

---

## 1. システム概要（現行設計）

- 通常枠テンプレート `T_ConsultationSlot` と日付マスタ `M_Date` から、ベース予定 `V_ScheduleBase` を生成
- 予定確認用に `V_ScheduleFull`（診療科/専門/医師/時間帯名を付加）を利用
- 通常枠変更 `T_ScheduleChange` と臨時外来 `T_TemporarySchedule` を統合した最終予定を `V_ScheduleActual` で提供
- 変更登録履歴画面で、通常枠変更・臨時外来の**検索/編集/CSV出力/テンプレートExcel反映出力**に対応
- 変更届の出力記録を `T_ChangeNoticeOutputHistory` に保存
- 各帳票ページは `sql/*.sql` を `streamlit_app/sql_loader.py` で読み込み実行
- ログは `streamlit_app/logging_config.py` で設定し、`logs/app.log` にローテーション保存

---

## 2. 主要データモデル

### 2.1 マスタ

- `M_ClinicalDepartment`（診療科、帳票フラグ `Rpt1Flag`〜`Rpt6Flag`）
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
  - 変更後医師・時間帯・部屋、変更内容、備考、`Rpt2Flag`、`ActiveFlag`
  - 同一日付・同一枠は**最新 `ChangeID`** を有効変更として扱う
- `T_TemporarySchedule`（臨時外来登録）
  - `Rpt1〜Rpt6` 系カラム、`Rpt2Flag`、`ActiveFlag` を保持
- `T_ChangeNoticeOutputHistory`（変更届出力履歴）
  - 出力対象種別、対象ID、出力者、出力日を保持

### 2.3 ビュー

- `V_ScheduleBase`
  - `M_Date` × `T_ConsultationSlot`
  - 有効期間・`WeekPattern`・`ActiveFlag` で絞り込み
  - `M_Holiday` で祝日除外
- `V_ScheduleFull`
  - `V_ScheduleBase` に診療科/専門/医師/時間帯名を付加（予定検索向け）
- `V_ScheduleActual`
  - 通常枠 + 最新変更（取消除外） + 臨時外来 を統合（反映後予定・帳票向け）

### 2.4 テーブル/ビュー カラム説明（現行DB定義ベース）
> 参照元: `sql/create_tables.sql`  
> `ID` は主キー、`ActiveFlag` は `1=有効 / 0=無効` 運用を想定。

#### M_ClinicalDepartment（診療科マスタ）

| カラム | 説明 |
|---|---|
| ClinDeptID | 診療科ID（主キー） |
| Category | 診療科カテゴリ |
| ClinDeptName | 診療科名 |
| Rpt1Sort | 帳票①での表示順 |
| Rpt1Flag | 帳票①の対象フラグ |
| Rpt2Flag | 帳票②の対象フラグ |
| Rpt3Flag | 帳票③の対象フラグ |
| Rpt4Flag | 帳票④の対象フラグ |
| Rpt5Flag | 帳票⑤の対象フラグ |
| Rpt6Flag | 帳票⑥の対象フラグ |
| ActiveFlag | 有効フラグ |

#### M_Specialty（専門マスタ）

| カラム | 説明 |
|---|---|
| SpecialtyID | 専門ID（主キー） |
| SpecialtyName | 専門名 |
| ActiveFlag | 有効フラグ |

#### M_ReportClinicalDepartment（帳票用診療科マスタ）

| カラム | 説明 |
|---|---|
| RptClinDeptID | 帳票用診療科ID（主キー） |
| RptClinDeptName | 帳票用診療科名 |
| ActiveFlag | 有効フラグ |

#### M_Doctor（医師マスタ）

| カラム | 説明 |
|---|---|
| DoctorID | 医師ID（主キー） |
| DoctorName | 医師名 |
| Department | 所属 |
| EmploymentType | 勤務形態（常勤/非常勤など） |
| ActiveFlag | 有効フラグ |

#### M_TimeSlot（時間帯マスタ）

| カラム | 説明 |
|---|---|
| TimeSlotID | 時間帯ID（主キー） |
| TimeSlotName | 時間帯名（午前/午後など） |

#### M_Date（日付マスタ）

| カラム | 説明 |
|---|---|
| DateID | 日付ID（主キー） |
| CalendarDate | カレンダー日付（YYYY-MM-DD） |
| DayOfWeek | 曜日番号（0-6） |
| WeekNumber | 月内週番号（1-5想定） |
| YearMonth | 年月（YYYY-MM） |

#### M_Holiday（祝日マスタ）

| カラム | 説明 |
|---|---|
| HolidayID | 祝日ID（主キー） |
| HolidayDate | 祝日の日付 |
| HolidayName | 祝日名 |

#### M_ScheduleChangeType（予定変更区分マスタ）

| カラム | 説明 |
|---|---|
| ChangeTypeID | 変更区分ID（主キー） |
| ChangeTypeName | 変更区分名（休診/代診など） |
| IsCancel | 取消区分（1=取消） |
| ActiveFlag | 有効フラグ |

#### T_ConsultationSlot（通常枠テンプレート）

| カラム | 説明 |
|---|---|
| SlotID | 枠ID（主キー） |
| Rpt1ClinDeptID | 帳票①用の診療科ID |
| Rpt1SpecialtyID | 帳票①用の専門ID |
| Rpt1DisplayDoctorName | 帳票①表示用の医師名（文字列） |
| Rpt2ClinDeptID | 帳票②用の診療科ID |
| Rpt3ClinDeptID | 帳票③用の診療科ID |
| Rpt4ClinDeptID | 帳票④用の診療科ID |
| Rpt5ClinDeptID | 帳票⑤用の診療科ID |
| Rpt6ClinDeptID | 帳票⑥用の診療科ID |
| DoctorID | 担当医師ID |
| TimeSlotID | 時間帯ID |
| Room | 診察室/部屋 |
| DayOfWeek | 適用曜日（`M_Date.DayOfWeek` と一致） |
| WeekPattern | 適用週パターン（例: `135` = 第1/3/5週） |
| StartDate | 有効開始日 |
| EndDate | 有効終了日 |
| ActiveFlag | 有効フラグ |

#### T_ScheduleChange（通常枠変更トランザクション）

| カラム | 説明 |
|---|---|
| ChangeID | 変更ID（主キー） |
| CalendarDate | 変更対象日 |
| SlotID | 変更対象の枠ID |
| ChangeTypeID | 変更区分ID |
| ChangeDetail | 変更内容メモ |
| NewDoctorID | 変更後医師ID |
| NewTimeSlotID | 変更後時間帯ID |
| NewRoom | 変更後部屋 |
| Reason | 変更理由 |
| ChangeAcceptedDate | 承認日 |
| ChangedBy | 変更者 |
| Rpt2Flag | 帳票②出力対象フラグ |
| ActiveFlag | 有効フラグ |
| CreatedAt | 作成日時 |

#### T_TemporarySchedule（臨時外来トランザクション）

| カラム | 説明 |
|---|---|
| TempID | 臨時外来ID（主キー） |
| CalendarDate | 実施日 |
| TimeSlotID | 時間帯ID |
| Rpt1ClinDeptID | 帳票①用の診療科ID |
| Rpt1SpecialtyID | 帳票①用の専門ID |
| Rpt1DisplayDoctorName | 帳票①表示用の医師名（文字列） |
| Rpt2ClinDeptID | 帳票②用の診療科ID |
| Rpt3ClinDeptID | 帳票③用の診療科ID |
| Rpt4ClinDeptID | 帳票④用の診療科ID |
| Rpt5ClinDeptID | 帳票⑤用の診療科ID |
| Rpt6ClinDeptID | 帳票⑥用の診療科ID |
| DoctorID | 担当医師ID |
| Room | 診察室/部屋 |
| ChangeDetail | 備考/変更内容 |
| Reason | 理由 |
| ActiveFlag | 有効フラグ |
| Rpt2Flag | 帳票②出力対象フラグ |
| CreatedAt | 作成日時 |

#### T_ChangeNoticeOutputHistory（変更届出力履歴）

| カラム | 説明 |
|---|---|
| OutputHistoryID | 出力履歴ID（主キー） |
| TargetType | 出力対象種別（ScheduleChange / TemporarySchedule） |
| TargetID | 出力対象のID（ChangeID / TempID） |
| OutputBy | 出力実行者 |
| OutputDate | 出力日時 |

#### V_ScheduleBase（通常枠展開ビュー）

| カラム | 説明 |
|---|---|
| CalendarDate | 展開後の日付 |
| DayOfWeek | 曜日番号 |
| WeekNumber | 月内週番号 |
| SlotID | 元テンプレートの枠ID |
| Rpt1ClinDeptID | 帳票①用診療科ID |
| Rpt1SpecialtyID | 帳票①用専門ID |
| Rpt1DisplayDoctorName | 帳票①表示用医師名 |
| Rpt2ClinDeptID | 帳票②用診療科ID |
| Rpt3ClinDeptID | 帳票③用診療科ID |
| Rpt4ClinDeptID | 帳票④用診療科ID |
| Rpt5ClinDeptID | 帳票⑤用診療科ID |
| Rpt6ClinDeptID | 帳票⑥用診療科ID |
| DoctorID | 担当医師ID |
| TimeSlotID | 時間帯ID |
| Room | 診察室/部屋 |

#### V_ScheduleFull（予定確認ビュー）

| カラム | 説明 |
|---|---|
| CalendarDate | 日付 |
| DayOfWeekNumber | 曜日番号（`strftime('%w')`） |
| DayOfWeek | 曜日表示（`月` など） |
| ClinDeptName | 診療科名 |
| SpecialtyName | 専門名 |
| TimeSlotName | 時間帯名 |
| Room | 診察室/部屋 |
| DoctorID | 医師ID |
| DoctorName | 医師名 |
| DisplayDoctorName | 帳票①表示用医師名 |
| SlotID | 元枠ID |

#### V_ScheduleActual（反映後予定ビュー）

| カラム | 説明 |
|---|---|
| CalendarDate | 日付 |
| SlotID | 元枠ID（臨時外来は `NULL`） |
| Rpt1ClinDeptID | 帳票①用診療科ID |
| Rpt1SpecialtyID | 帳票①用専門ID |
| Rpt1DisplayDoctorName | 帳票①表示用医師名 |
| Rpt2ClinDeptID | 帳票②用診療科ID |
| Rpt3ClinDeptID | 帳票③用診療科ID |
| Rpt4ClinDeptID | 帳票④用診療科ID |
| Rpt5ClinDeptID | 帳票⑤用診療科ID |
| Rpt6ClinDeptID | 帳票⑥用診療科ID |
| DoctorID | 最終採用医師ID（変更後優先） |
| TimeSlotID | 最終採用時間帯ID（変更後優先） |
| Room | 最終採用部屋（変更後優先） |
| ChangeTypeID | 変更区分ID（臨時外来は `NULL`） |
| ChangeDetail | 変更内容/備考 |
| Reason | 変更理由 |

---

## 3. 画面構成（`streamlit_app/pages`）

1. **枠管理**（`1_枠管理.py`）
2. **予定検索**（`2_予定検索.py`）
3. **予定変更入力**（`3_予定変更入力.py`）
4. **反映後予定検索**（`4_反映後予定検索.py`）
5. **変更登録履歴検索**（`5_変更登録履歴.py`）
   - 履歴一覧・編集
   - 条件絞り込み + 出力対象チェック
   - テンプレートExcel（プレースホルダ）への反映出力
   - 出力時の履歴保存
6. **帳票① 外来担当医表**（`6_帳票1.py`）
7. **帳票② 予定変更一覧**（`7_帳票2.py`）
8. **帳票③ 外来数**（`8_帳票3.py`）
9. **帳票④ 常勤日別コマ数**（`9_帳票4.py`）
10. **帳票⑤ 常勤・非常勤月別コマ数**（`10_帳票5.py`）
11. **帳票⑥ 非常勤医師勤務報告書**（`11_帳票6.py`）
12. **マスタ管理**（`12_マスタ管理.py`）
   - 各種マスタ編集に加え、**年度管理タブ**から次年度/指定年度範囲の追加が可能

サイドバーには、Windowsサーバー向けに **「💾 バックアップして終了」** ボタンがあります。

---

## 4. SQL/スクリプト構成

### 4.1 `sql/`

- `create_tables.sql`（全テーブル・ビュー定義）
- 帳票SQL
  - `Report1_pivot.sql`
  - `Report1_pivot_external.sql`
  - `Report2.sql`
  - `Report3.sql`
  - `Report4.sql`
  - `Report5.sql`
  - `Report6_daily_status.sql`
  - `Report6_eligible_doctors.sql`

### 4.2 `scripts/`

- `init_db.py`（DB初期化）
- `import_master_csv.py`（マスタCSV取込）
- `generate_date_master.py`（日付マスタ生成）
- `generate_holiday_master.py`（祝日マスタ生成）
- `import_consultation_slot.py`（初期枠取込）
- `fix_date_format.py`（日付補正）
- `migrate.py`（既存DBへのマイグレーション）

---

## 4.3 保守引継ぎ（要約）

引継ぎ資料は、次の2層構成を推奨します。

1. **README（本書）**
   - 全体像・導線・主要ディレクトリを短く把握する入口
2. **詳細マップ（別ドキュメント）**
   - `docs/保守引継ぎ_ページ関連マップ.md`
   - SQL / scripts / Streamlitページ間の依存関係、変更影響チェックを詳細化

また、担当者向けの操作資料は `docs/担当者マニュアル.md` を正本とし、
画面スクリーンショット付き手順を継続追記する運用を推奨します。

---

## 5. 初期セットアップ

> 前提: Python 3.11 以上推奨

### 5.0 新規環境への導入手順（配布済み原本をPCへ配置）

開発完了後は、GitHub から `git clone` する運用ではなく、  
**GitHub上で保持しているディレクトリ構成をコピーした「配布用原本」**をファイルサーバー等で管理し、  
PCセットアップ時にその一式をサーバーPCへコピーして導入する想定です。  
以下を「新規環境の標準手順」として利用してください。

1. 配布用原本（フォルダ一式）をサーバーPCへコピーする  
   （`Schedule-System/` 一式をそのまま配置）

```bash
cd Schedule-System
```

2. `csv/` フォルダ配下にマスタCSV一式を配置する  
   （例: `M_*.csv`, `T_ConsultationSlot.csv`）

3. 初期セットアップを実行する（推奨: 自動化バッチ）

- Windows (cmd.exe)

```bat
ops\windows\init_setup.bat
```

> 上記バッチで、以下 4 手順（仮想環境作成 / 仮想環境利用 / 依存インストール / `set_up.py` 実行）を連続実行します。

4. （手動実行する場合）仮想環境を作成する

```bash
python -m venv venv
```

5. （手動実行する場合）仮想環境を有効化する

- Windows (PowerShell)

```powershell
.\venv\Scripts\Activate.ps1
```

- Windows (cmd.exe)

```bat
.\venv\Scripts\activate
```

6. （手動実行する場合）依存関係をインストールする

```bat
venv\Scripts\python.exe -m pip install -r requirements.txt
```

7. （手動実行する場合）初期セットアップを実行する

```bat
venv\Scripts\python.exe set_up.py
```

### 5.1 依存インストール（個別実行したい場合）

```bat
venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 5.2 DB・初期データ作成

```bat
venv\Scripts\python.exe set_up.py
```

`set_up.py` 実行内容:

1. `scripts/init_db.py`
2. `scripts/import_master_csv.py`
3. `scripts/generate_date_master.py`
4. `scripts/generate_holiday_master.py`
5. `scripts/import_consultation_slot.py`
6. `scripts/fix_date_format.py`
7. `scripts/migrate.py`

### 5.3 年度の追加（運用時）

#### 方法A: 設定値を更新して再実行

`scripts/settings.py` の `END_FISCAL_YEAR` を更新し、再実行します。

```bat
venv\Scripts\python.exe set_up.py
```

または対象スクリプトのみ:

```bat
venv\Scripts\python.exe scripts/generate_date_master.py
venv\Scripts\python.exe scripts/generate_holiday_master.py
```

#### 方法B: 追加年度だけを生成（推奨）

既存データの最大年度の次年度を1年追加:

```bat
venv\Scripts\python.exe scripts/extend_fiscal_year.py
```

範囲指定で追加（例: 2031〜2033年度）:

```bat
venv\Scripts\python.exe scripts/extend_fiscal_year.py --start-fy 2031 --end-fy 2033
```

> `M_Date` は `INSERT OR IGNORE`、`M_Holiday` は `WHERE NOT EXISTS` で重複追加を回避します。

### 5.4 起動

```bat
venv\Scripts\python.exe -m streamlit run streamlit_app/app.py
```

### 5.5 別PCへの導入時の注意（バックアップ復元）

1. 先にバックアップDB（`schedule.db`）を復元する  
2. その後に必要があれば `scripts/extend_fiscal_year.py` で不足年度のみ追加する  

この順序にすると、復元済み年度とセットアップ既定年度の差異があっても、重複や欠損のリスクを最小化できます。

---

## 6. 運用ルール（重要）

### 6.1 診療科名の基準と帳票別名称切替

- `M_ClinicalDepartment`
  - `Rpt1Flag`〜`Rpt6Flag` で帳票ごとの出力対象を制御
  - `Rpt1Sort` で帳票①の表示順を制御
- `T_ConsultationSlot`
  - `Rpt1ClinDeptID` をベース診療科（帳票①基準）として保持
  - `Rpt2ClinDeptID`〜`Rpt6ClinDeptID` を帳票別の表示切替キーとして保持
- `M_ReportClinicalDepartment`
  - 帳票②〜⑥向けの診療科表示名（必要に応じて専門外来名運用を含む）を定義

次の4画面では、ベースとして `T_ConsultationSlot.Rpt1ClinDeptID` を使用します。

- `2_予定検索.py`
- `3_予定変更入力.py`
- `4_反映後予定検索.py`
- `5_変更登録履歴.py`

### 6.2 その他のデータ運用ルール

- 終了日未定は `9999-12-31` を使用
- 帳票キーは `T_ConsultationSlot` / `T_TemporarySchedule` の `Rpt1〜Rpt6` 系カラムで管理
- 予定変更反映は「同一日・同一枠の最新変更（最新 `ChangeID`）」を採用
- 帳票②表示制御には `Rpt2Flag` を使用
- 祝日除外は `V_ScheduleBase` 生成時点で適用
- 変更登録履歴画面で `ActiveFlag` の切替が可能（無効化データの再表示可）

---

## 7. ディレクトリ構成

```text
Schedule-System/
├─ README.md
├─ database/  （実行時生成・Git管理外）
│  └─ schedule.db
├─ csv/  （運用データ配置・Git管理外）
│  ├─ M_*.csv
│  └─ T_ConsultationSlot.csv
├─ docs/
│  └─ 担当者マニュアル.md
├─ logs/  （実行時生成・Git管理外）
├─ backups/  （バックアップ先・Git管理外）
├─ .runtime/  （ランタイム一時領域・Git管理外）
├─ requirements.txt
├─ set_up.py
├─ scripts/
├─ sql/
├─ ops/
│  └─ windows/
│     ├─ init_setup.bat
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
  - `streamlit_app/app.py` をバックグラウンド起動
  - ブラウザ（Edge/Chrome）を専用ウィンドウで開く

### 9.2 バックアップ

- `backup_db.bat`
  - `database/schedule.db` を `backups/schedule_yyyyMMdd_HHmmss.db` へコピー
  - 30日より古いバックアップを自動削除

### 9.3 停止

- `stop_app.bat`
  - ポート `8501` の待受プロセスを停止
  - 起動時の専用ブラウザウィンドウも終了対象

### 9.4 URL

- 同一PC: `http://localhost:8501`
- 他端末: `http://<運用PC名>:8501`

---

## 10. 担当者向けドキュメント

日次運用手順・画面別操作の詳細は `docs/担当者マニュアル.md` を参照してください。

---

## 11. ログ仕様ドキュメント

ログ出力機能の仕様（イベント一覧、主要フィールド、運用時の確認ポイント）は  
`docs/ログ出力仕様.md` を参照してください。

---

## 12. 保守担当者向け 障害対応ドキュメント

障害発生時の一次切り分け手順（事象別の確認ポイント、エスカレーション基準）は  
`docs/障害対応手順.md` を参照してください。

- README: 全体概要・導線
- ログ仕様書: 詳細定義（運用・保守向け）
