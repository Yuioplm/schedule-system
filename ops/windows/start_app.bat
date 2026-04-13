@echo off
setlocal

REM Move to repository root (this bat is in ops\windows)
cd /d "%~dp0..\.."

echo [INFO] Starting Schedule System...

if not exist "streamlit_app\app.py" goto no_app

set "PYTHON_EXE=%CD%\venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
  set "VENV_NAME=venv"
  goto have_venv
)

set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
  set "VENV_NAME=.venv"
  goto have_venv
)

goto create_venv

:have_venv
echo [INFO] Using virtual environment (%VENV_NAME%): %PYTHON_EXE%

"%PYTHON_EXE%" -c "import streamlit" >nul 2>&1
if errorlevel 1 goto install_requirements
goto run_app

:install_requirements
echo [WARN] streamlit is not installed in this venv.
echo [INFO] Installing dependencies from requirements.txt ...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 goto install_failed

:run_app
echo [INFO] Launching app in background (hidden console) ...
powershell -NoProfile -ExecutionPolicy Bypass ^
  -Command "Start-Process -FilePath '%PYTHON_EXE%' -ArgumentList '-m streamlit run streamlit_app/app.py --server.address 0.0.0.0 --server.port 8501' -WorkingDirectory '%CD%' -WindowStyle Hidden"
if errorlevel 1 goto launch_failed

echo [INFO] Startup command issued.
echo [INFO] Open: http://localhost:8501
exit /b 0

:no_app
echo [ERROR] streamlit_app\app.py not found.
echo [ERROR] Please place this script under ops\windows in the repository.
pause
exit /b 1

:create_venv
echo [WARN] venv/.venv was not found. Creating virtual environment at "venv"...
where py >nul 2>&1
if not errorlevel 1 goto create_venv_with_py
where python >nul 2>&1
if not errorlevel 1 goto create_venv_with_python
echo [ERROR] Python launcher was not found.
echo [HINT] Install Python 3.11+ and run this script again.
pause
exit /b 1

:create_venv_with_py
py -3 -m venv venv
if errorlevel 1 goto venv_failed
goto venv_created

:create_venv_with_python
python -m venv venv
if errorlevel 1 goto venv_failed
goto venv_created

:venv_created
set "VENV_NAME=venv"
set "PYTHON_EXE=%CD%\venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" goto venv_failed
echo [INFO] Virtual environment created (%VENV_NAME%): %PYTHON_EXE%
goto install_requirements

:venv_failed
echo [ERROR] Failed to create virtual environment.
echo [HINT] Run manually:
echo        py -3 -m venv venv
echo        venv\Scripts\python.exe -m pip install -r requirements.txt
pause
exit /b 1

:install_failed
echo [ERROR] Failed to install requirements.
echo [HINT] Please check network/proxy settings and run manually:
echo        "%PYTHON_EXE%" -m pip install -r requirements.txt
pause
exit /b 1

:launch_failed
echo [ERROR] Failed to launch Streamlit.
echo [HINT] Run set_up.py once and check package installation.
pause
exit /b 1
