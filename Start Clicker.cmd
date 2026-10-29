@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" desktop.py
) else (
    py -3 desktop.py
)
if errorlevel 1 (
    echo.
    echo Could not start. Follow the Windows setup steps in README.md.
    pause
)
