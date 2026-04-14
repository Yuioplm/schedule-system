@echo off
setlocal

REM Move to repository root (this bat is in ops\windows)
cd /d "%~dp0..\.."

set "PORT=8501"
set "URL=http://localhost:%PORT%"
set "RUNTIME_DIR=%CD%\.runtime"
set "BROWSER_PID_FILE=%RUNTIME_DIR%\browser.pid"
set "BROWSER_PROFILE_DIR=%RUNTIME_DIR%\browser_profile"

echo [INFO] Starting Schedule System...

if not exist "streamlit_app\app.py" goto no_app

REM If app is already running, only open browser.
netstat -ano | findstr ":%PORT%" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 goto app_already_running

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
  -Command "Start-Process -FilePath '%PYTHON_EXE%' -ArgumentList '-m streamlit run streamlit_app/app.py --server.address 0.0.0.0 --server.port %PORT% --server.headless true' -WorkingDirectory '%CD%' -WindowStyle Hidden"
if errorlevel 1 goto launch_failed

echo [INFO] Startup command issued.
echo [INFO] Opening browser window: %URL%
call :open_browser_window
exit /b 0

:app_already_running
echo [INFO] App is already running on port %PORT%.
echo [INFO] Opening browser window: %URL%
call :open_browser_window
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

:open_browser_window
if not exist "%RUNTIME_DIR%" mkdir "%RUNTIME_DIR%"
if not exist "%BROWSER_PROFILE_DIR%" mkdir "%BROWSER_PROFILE_DIR%"

set "BROWSER_EXE="
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
  set "BROWSER_EXE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
) else if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
  set "BROWSER_EXE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
) else if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
  set "BROWSER_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
) else if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
  set "BROWSER_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
)

if not "%BROWSER_EXE%"=="" goto open_app_browser

echo [WARN] Edge/Chrome が見つからないため、既定ブラウザで開きます。
start "" "%URL%"
exit /b 0

:open_app_browser
powershell -NoProfile -ExecutionPolicy Bypass ^
  -Command "$p = Start-Process -FilePath '%BROWSER_EXE%' -ArgumentList '--new-window','--app=%URL%','--user-data-dir=%BROWSER_PROFILE_DIR%' -PassThru; $p.Id | Set-Content -Path '%BROWSER_PID_FILE%' -Encoding ascii"
if errorlevel 1 (
  echo [WARN] 専用ウィンドウ起動に失敗したため、既定ブラウザで開きます。
  start "" "%URL%"
  exit /b 0
)

exit /b 0
