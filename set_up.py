import subprocess
import sys

from streamlit_app.logging_config import setup_logger

logger = setup_logger("setup")


def run(script: str) -> None:
    print(f"\nRunning {script}")
    logger.info("setup_script_start script=%s", script)

    subprocess.run([sys.executable, script], check=True)

    logger.info("setup_script_success script=%s", script)


def main() -> None:
    print("====== Schedule System Setup ======")
    logger.info("setup_start")

    run("scripts/init_db.py")
    run("scripts/import_master_csv.py")
    run("scripts/generate_date_master.py")
    run("scripts/generate_holiday_master.py")
    run("scripts/import_consultation_slot.py")
    run("scripts/fix_date_format.py")
    run("scripts/migrate.py")

    print("\n====== Setup Completed ======")
    logger.info("setup_completed")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("setup_failed")
        raise
