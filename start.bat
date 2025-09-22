@echo off

rem use path of this batch file as working directory; enables starting this script from anywhere
cd /d "%~dp0"

call .venv\Scripts\activate 

rem create directory for user data
if not exist ".user" mkdir .user

if "%1"=="dev" (
	echo Starting Uvicorn server in development mode...
    rem Set debug logging
    set LOGURU_LEVEL=DEBUG
    set UVICORN_LOG_LEVEL=debug
    rem reload implies workers = 1
	echo starting server at port 9015
    uvicorn beaverhabits.main:app --reload --log-level warning --port 9015 --host 0.0.0.0
	
) else (
    echo Starting Uvicorn server in production mode...
    rem Set nicegui storage path to avoid permission issues if not already set
    if "%NICEGUI_STORAGE_PATH%"=="" set NICEGUI_STORAGE_PATH=.user\.nicegui
    rem we use a single worker in production mode so socket.io connections are always handled by the same worker
	set LOGURU_LEVEL=WARNING
	set UVICORN_LOG_LEVEL=warning
    uvicorn beaverhabits.main:app --workers 1 --log-level warning --port 9015 --host 0.0.0.0
)
