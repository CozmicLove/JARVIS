@echo off
setlocal

cd /d "%~dp0"

timeout /t 5 /nobreak >nul
wscript.exe "%~dp0start_nova_hidden.vbs"
