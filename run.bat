@echo off
chcp 65001 >nul
setlocal
set "PYTHONDONTWRITEBYTECODE=1"

if "%OPENCLUELY_HOME%"=="" if defined LOCALAPPDATA set "OPENCLUELY_HOME=%LOCALAPPDATA%\Opencluely"

echo.
echo =====================================
echo   Opencluely
echo =====================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on PATH.
    echo Install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Checking desktop dependencies...
python -B -c "import PySide6" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing Python dependencies from requirements.txt
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
)

echo Launching Opencluely...
if defined OPENCLUELY_HOME echo Runtime files will be written under: %OPENCLUELY_HOME%
echo.

python -B main.py

echo.
echo Application finished.
pause
