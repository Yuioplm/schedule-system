import subprocess
import sys

def run(script):

    print(f"\nRunning {script}")

    subprocess.run([sys.executable, script], check=True)

def main():

    print("====== Schedule System Setup ======")

    run("scripts/init_db.py")

    run("scripts/import_master_csv.py")

    run("scripts/generate_date_master.py")

    run("scripts/generate_holiday_master.py")

    run("scripts/import_consultation_slot.py")

    run("scripts/fix_date_format.py")

    run("scripts/generate_schedule.py")

    print("\n====== Setup Completed ======")

if __name__ == "__main__":
    main()