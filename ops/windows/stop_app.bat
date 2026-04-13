@echo off
setlocal

set "PORT=8501"
set "FOUND=0"

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

endlocal
