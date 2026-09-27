@echo off
setlocal

cd /d "%~dp0"

if not exist "kokoro_env\Scripts\python.exe" (
    echo NOVA cannot find kokoro_env\Scripts\python.exe
    echo Please make sure the NOVA environment exists.
    pause
    exit /b 1
)

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

"kokoro_env\Scripts\python.exe" "src\ui\control_center.py"

if errorlevel 1 (
    echo.
    echo NOVA stopped with an error.
    pause
)
