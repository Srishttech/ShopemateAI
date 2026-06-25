#!/bin/bash

clear

echo "=========================================="
echo "         SHOPMATE AI LAUNCHER"
echo "=========================================="
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed."
    echo "Please install Python 3.11 or later."
    exit 1
fi

# Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "[+] Creating Virtual Environment..."
    python3 -m venv venv
fi

# Activate Virtual Environment
source venv/bin/activate

# Upgrade pip
echo
echo "[+] Upgrading pip..."
python -m pip install --upgrade pip

# Install Dependencies
echo
echo "[+] Installing Requirements..."
pip install -r requirements.txt

# Create .env if missing
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        echo "GROQ_API_KEY=your_api_key_here" > .env
    fi

    echo
    echo "*********************************************"
    echo "Please edit the .env file and add your"
    echo "GROQ_API_KEY before using the application."
    echo "*********************************************"
    exit 0
fi

# Launch Streamlit
echo
echo "[+] Starting Application..."
streamlit run app.py --server.address=0.0.0.0 --server.port=8501 --server.enableCORS=false --server.enableXsrfProtection=false
