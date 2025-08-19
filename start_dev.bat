@echo off

rem use path of this batch file as working directory; enables starting this script from anywhere
cd /d "%~dp0"

call .venv\Scripts\activate 

rem create directory for user data
if not exist ".user" mkdir .user

echo Starting Uvicorn server in development mode...
rem Set debug logging
set LOGURU_LEVEL=DEBUG
set UVICORN_LOG_LEVEL=debug
rem reload implies workers = 1
uvicorn beaverhabits.main:app --reload --log-level warning --port 9015 --host 0.0.0.0
