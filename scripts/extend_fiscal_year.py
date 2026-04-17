import argparse
import os
import subprocess
import sys

from settings import BASE_DIR, get_conn_context


def detect_existing_fiscal_year_range() -> tuple[int | None, int | None]:
    with get_conn_context() as conn:
        row = conn.execute("""
            SELECT
                MIN(
                    CASE
                        WHEN CAST(strftime('%m', CalendarDate) AS INTEGER) >= 4
                            THEN CAST(strftime('%Y', CalendarDate) AS INTEGER)
                        ELSE CAST(strftime('%Y', CalendarDate) AS INTEGER) - 1
                    END
                ) AS min_fy,
                MAX(
                    CASE
                        WHEN CAST(strftime('%m', CalendarDate) AS INTEGER) >= 4
                            THEN CAST(strftime('%Y', CalendarDate) AS INTEGER)
                        ELSE CAST(strftime('%Y', CalendarDate) AS INTEGER) - 1
                    END
                ) AS max_fy
            FROM M_Date
        """).fetchone()
    return row[0], row[1]


def run_generator(script_name: str, start_fy: int, end_fy: int) -> None:
    env = os.environ.copy()
    env["START_FISCAL_YEAR"] = str(start_fy)
    env["END_FISCAL_YEAR"] = str(end_fy)
    script_path = BASE_DIR / "scripts" / script_name
    subprocess.run([sys.executable, str(script_path)], env=env, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="M_Date/M_Holiday に会計年度レンジを追加生成します（重複はスキップ）。"
    )
    parser.add_argument("--start-fy", type=int, help="追加開始会計年度（例: 2031）")
    parser.add_argument("--end-fy", type=int, help="追加終了会計年度（例: 2033）")
    args = parser.parse_args()

    existing_min_fy, existing_max_fy = detect_existing_fiscal_year_range()

    if args.start_fy is not None and args.end_fy is None:
        target_start_fy = args.start_fy
        target_end_fy = args.start_fy
    elif args.start_fy is None and args.end_fy is not None:
        if existing_max_fy is None:
            raise ValueError("既存M_Dateが空のため、--start-fy も指定してください。")
        target_start_fy = existing_max_fy + 1
        target_end_fy = args.end_fy
    elif args.start_fy is None and args.end_fy is None:
        if existing_max_fy is None:
            raise ValueError("既存M_Dateが空のため、--start-fy を指定してください。")
        target_start_fy = existing_max_fy + 1
        target_end_fy = target_start_fy
    else:
        target_start_fy = args.start_fy
        target_end_fy = args.end_fy

    if target_start_fy > target_end_fy:
        raise ValueError("--start-fy は --end-fy 以下を指定してください。")

    print(
        f"[extend_fiscal_year] existing_fy={existing_min_fy}..{existing_max_fy}, "
        f"append_fy={target_start_fy}..{target_end_fy}"
    )
    run_generator("generate_date_master.py", target_start_fy, target_end_fy)
    run_generator("generate_holiday_master.py", target_start_fy, target_end_fy)
    print("[extend_fiscal_year] completed")


if __name__ == "__main__":
    main()
