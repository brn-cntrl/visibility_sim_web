@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Visibility Simulator - Installation
echo ========================================
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo Please install Python 3.11 from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION%

REM Check Node.js
echo.
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Node.js not found.
    echo.
    echo Please install Node.js from: https://nodejs.org/
    echo Download the LTS version and run the installer.
    echo After installation, restart this script.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js %NODE_VERSION%

REM Check npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo [OK] npm %NPM_VERSION%

REM Check C++ compiler
echo.
echo Checking C++ compiler...
cl /? >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Visual Studio C++ compiler not found.
    echo.
    echo You need Visual Studio Build Tools to compile the C++ module.
    echo Download from: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
    echo.
    echo Install "Desktop development with C++" workload
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "!continue!"=="y" exit /b 1
) else (
    echo [OK] Visual Studio C++ compiler found
)

REM Install Python dependencies
echo.
echo Installing Python dependencies...
pip install Flask==3.1.0 flask-cors==6.0.1 Werkzeug==3.1.3 pybind11
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [OK] Python dependencies installed

REM Build C++ visibility module
echo.
echo Building C++ visibility module...
if not exist setup.py (
    echo [ERROR] setup.py not found
    pause
    exit /b 1
)

python setup.py build_ext --inplace
if errorlevel 1 (
    echo [ERROR] C++ module build failed
    echo.
    echo Make sure you have Visual Studio Build Tools installed:
    echo https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
    pause
    exit /b 1
)

REM Verify .pyd file exists
dir /b visibility_polygon*.pyd >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Built module not found
    pause
    exit /b 1
)
echo [OK] C++ module built successfully

REM Install React dependencies
echo.
echo Installing React dependencies...
if not exist frontend (
    echo [ERROR] frontend directory not found
    pause
    exit /b 1
)

cd frontend
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install React dependencies
    cd ..
    pause
    exit /b 1
)
cd ..
echo [OK] React dependencies installed

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To start the application:
echo.
echo   Terminal 1 (Backend):
echo     python app.py
echo.
echo   Terminal 2 (Frontend):
echo     cd frontend
echo     npm start
echo.
echo Then open http://localhost:3000 in your browser
echo.
pause