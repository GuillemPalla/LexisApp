@echo off
setlocal

set APP_DIR=%~dp0

start "" "%APP_DIR%python\pythonw.exe" "%APP_DIR%app\serve.py"

:WAIT_LOOP
timeout /t 1 /nobreak >nul
"%APP_DIR%python\python.exe" -c "import urllib.request; urllib.request.urlopen('http://localhost:8000')" 2>nul
if errorlevel 1 goto WAIT_LOOP

start "" http://localhost:8000