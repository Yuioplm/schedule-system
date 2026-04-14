@echo off
setlocal

REM Move to repository root (this bat is in ops\windows)
cd /d "%~dp0..\.."

set "PORT=8501"
set "FOUND=0"
set "RUNTIME_DIR=%CD%\.runtime"
set "BROWSER_PID_FILE=%RUNTIME_DIR%\browser.pid"
set "BROWSER_PROFILE_DIR=%RUNTIME_DIR%\browser_profile"

echo [INFO] Stopping Streamlit process on port %PORT% ...

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
  set "FOUND=1"
  echo [INFO] Killing PID %%p
  taskkill /PID %%p /F >nul 2>&1
)

if "%FOUND%"=="0" (
  echo [INFO] No LISTENING process found on port %PORT%.
) else (
  echo [INFO] Stop completed.
)

if exist "%BROWSER_PID_FILE%" (
  set /p BROWSER_PID=<"%BROWSER_PID_FILE%"
  if not "%BROWSER_PID%"=="" (
    echo [INFO] Closing app browser window PID %BROWSER_PID% ...
    taskkill /PID %BROWSER_PID% /T /F >nul 2>&1
  )
  del /q "%BROWSER_PID_FILE%" >nul 2>&1
)

if exist "%BROWSER_PROFILE_DIR%" (
  echo [INFO] Closing browser processes bound to %BROWSER_PROFILE_DIR% ...
  powershell -NoProfile -ExecutionPolicy Bypass ^
    -Command "$profile = '%BROWSER_PROFILE_DIR%'; Get-CimInstance Win32_Process | Where-Object { ($_.Name -ieq 'msedge.exe' -or $_.Name -ieq 'chrome.exe') -and $_.CommandLine -and $_.CommandLine.Contains($profile) } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
)

endlocal
