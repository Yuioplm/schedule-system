@echo off
setlocal

REM Move to repository root (this bat is in ops\windows)
cd /d "%~dp0..\.."

echo [INFO] Initial setup started...

if not exist "requirements.txt" goto no_requirements
if not exist "set_up.py" goto no_setup
if not exist "csv" goto no_csv

set "PYTHON_EXE=%CD%\venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" goto have_python

echo [INFO] Creating virtual environment at "venv"...
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -m venv venv
) else (
  python -m venv venv
)
if errorlevel 1 goto venv_failed

set "PYTHON_EXE=%CD%\venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" goto venv_failed

:have_python
echo [INFO] Using Python: %PYTHON_EXE%

echo [INFO] Installing dependencies from requirements.txt ...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 goto pip_failed

echo [INFO] Running initial setup (python set_up.py) ...
"%PYTHON_EXE%" set_up.py
if errorlevel 1 goto setup_failed

echo [INFO] Initial setup completed successfully.
exit /b 0

:no_requirements
echo [ERROR] requirements.txt not found.
echo [HINT] Please run this script from the repository's ops\windows folder.
pause
exit /b 1

:no_setup
echo [ERROR] set_up.py not found.
echo [HINT] Please run this script from the repository's ops\windows folder.
pause
exit /b 1

:no_csv
echo [ERROR] csv folder not found.
echo [HINT] Place master CSV files under csv\ and rerun this script.
pause
exit /b 1

:venv_failed
echo [ERROR] Failed to create virtual environment.
echo [HINT] Install Python 3.11+ and run this script again.
pause
exit /b 1

:pip_failed
echo [ERROR] Failed to install requirements.
echo [HINT] Check network/proxy and retry.
pause
exit /b 1

:setup_failed
echo [ERROR] set_up.py failed.
echo [HINT] Confirm csv files and database write permissions.
pause
exit /b 1

