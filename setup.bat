@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=python"
where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo Python 3.11 or newer is required. Install it from https://www.python.org/downloads/
        exit /b 1
    )
    set "PYTHON=py -3"
)

%PYTHON% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if errorlevel 1 (
    echo Python 3.11 or newer is required.
    exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
    echo Node.js 18 or newer is required. Install it from https://nodejs.org/
    exit /b 1
)
node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 18 ? 0 : 1)" >nul 2>nul
if errorlevel 1 (
    echo Node.js 18 or newer is required.
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo npm is required. Reinstall Node.js from https://nodejs.org/ with npm included.
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    %PYTHON% -m venv .venv
    if errorlevel 1 exit /b 1
)

echo Installing backend dependencies...
".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 exit /b 1

echo Installing frontend dependencies...
call npm --prefix frontend ci
if errorlevel 1 exit /b 1

if not exist ".env" if exist ".env.example" (
    copy ".env.example" ".env" >nul
    if errorlevel 1 exit /b 1
    echo Created .env from .env.example; add your credentials before starting the app.
)

echo.
echo Setup Complete!
echo Start the full stack with: docker compose up --build
echo For local development, start the backend with:
echo   .venv\Scripts\python.exe -m uvicorn backend.main:app --reload
echo Then start the frontend in another terminal with:
echo   cd frontend ^&^& npm run dev
endlocal
