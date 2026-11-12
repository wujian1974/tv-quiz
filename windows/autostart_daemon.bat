@echo off
REM 开机自启包装：最小化启动守护，不弹黑窗口。
REM 放到 Windows「启动」目录，或写进注册表
REM HKCU\Software\Microsoft\Windows\CurrentVersion\Run 均可。
set "ROOT=%~dp0.."
if not exist "%ROOT%\tools\tv_quiz_daemon.py" set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PY=python"
where python >nul 2>&1
if errorlevel 1 set "PY=py"
start "TV Quiz Daemon" /min "%PY%" tools\tv_quiz_daemon.py
