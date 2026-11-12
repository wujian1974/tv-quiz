@echo off
REM 双击启动守护。可加参数：--dry-run（只观察）、--fast 30（演示）、
REM --minutes 15（临时改间隔）、--no-gate（联调时临时关进门题）。
REM 本文件不含任何本机绝对路径，可直接放到项目根目录使用。
set "ROOT=%~dp0.."
if not exist "%ROOT%\tools\tv_quiz_daemon.py" set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PY=python"
where python >nul 2>&1
if errorlevel 1 set "PY=py"
"%PY%" tools\tv_quiz_daemon.py %*
echo.
echo Daemon stopped. Press any key to close.
pause >nul
