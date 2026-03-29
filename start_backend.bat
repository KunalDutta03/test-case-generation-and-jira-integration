@echo off
echo Starting TestGen AI Backend...
echo.
cd /d "%~dp0backend"
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing dependencies...
pip install -r requirements.txt -q
echo.
echo Starting FastAPI server on http://localhost:8000
echo Swagger UI: http://localhost:8000/api/docs
echo.
python main.py

