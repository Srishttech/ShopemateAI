@echo off
title ShopMate AI Launcher
color 0A

echo ==========================================
echo         SHOPMATE AI LAUNCHER
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo Please install Python 3.11 or later.
    echo https://www.python.org/downloads/
    pause
    exit /b
)

:: Create Virtual Environment
if not exist "venv" (
    echo [+] Creating Virtual Environment...
    python -m venv venv
)

:: Activate Virtual Environment
call venv\Scripts\activate.bat

:: Upgrade pip
echo.
echo [+] Upgrading pip...
python -m pip install --upgrade pip

:: Install Dependencies
echo.
echo [+] Installing Requirements...
pip install -r requirements.txt

:: Create .env if missing
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
    ) else (
        echo GROQ_API_KEY=your_api_key_here>.env
    )

    echo.
    echo *********************************************
    echo Please edit the .env file and add your
    echo GROQ_API_KEY before using the application.
    echo *********************************************
    pause
)

:: Launch Streamlit
echo.
echo [+] Starting Application...
streamlit run app.py

pause