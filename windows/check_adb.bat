@echo off
REM 自检：电视的网络 ADB 是否还开着（重启后可能被系统关掉）。
chcp 65001 >nul
set "ROOT=%~dp0.."
if not exist "%ROOT%\tools\check_adb.py" set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PY=python"
where python >nul 2>&1
if errorlevel 1 set "PY=py"
"%PY%" tools\check_adb.py
echo.
pause
