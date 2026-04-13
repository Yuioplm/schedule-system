@echo off
setlocal EnableDelayedExpansion

REM Move to repository root (this bat is in ops\windows)
cd /d "%~dp0..\.."

set "DB_PATH=database\schedule.db"
set "BACKUP_DIR=backups"

if not exist "%DB_PATH%" (
  echo [ERROR] Database file not found: %DB_PATH%
  exit /b 1
)

if not exist "%BACKUP_DIR%" (
  mkdir "%BACKUP_DIR%"
)

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%i"
set "DEST=%BACKUP_DIR%\schedule_!STAMP!.db"

copy "%DB_PATH%" "%DEST%" >nul
if errorlevel 1 (
  echo [ERROR] Backup failed.
  exit /b 1
)

echo [INFO] Backup created: %DEST%

REM Delete backup files older than 30 days
forfiles /p "%BACKUP_DIR%" /m "schedule_*.db" /d -30 /c "cmd /c del /q @path" >nul 2>&1
echo [INFO] Cleanup finished (older than 30 days removed).

endlocal
