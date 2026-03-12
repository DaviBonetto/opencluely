@echo off
chcp 65001 >nul
setlocal

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

if not exist logs mkdir logs >nul 2>&1

echo Checking desktop dependencies...
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing Python dependencies from requirements.txt
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
)

tesseract --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Tesseract was not found. Screenshot OCR will stay disabled.
    echo        Download from https://github.com/UB-Mannheim/tesseract/wiki
    echo.
)

if "%GROQ_API_KEY%"=="" (
    echo [WARN] GROQ_API_KEY is not configured.
    echo        Live transcription and Assist responses will be unavailable.
    echo        Create a key at https://console.groq.com/keys
    echo.
)

echo Launching Opencluely...
echo Logs will be written to the logs\ directory.
echo.

python main.py

echo.
echo Application finished.
pause
